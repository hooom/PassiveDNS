#!/bin/env python
#coding=utf8
import re
import sys
import os
import time
import traceback
import glob
import fcntl
import commands
import hashlib
import codecs
import linecache
import datetime
from pymongo import MongoClient
reload(sys)
sys.setdefaultencoding('utf8')

DNS_DATA_DIRECTORY = r'/home/houman/txt/*.txt'
last_swap_out_time = datetime.datetime.now()
RecordValueCache = {}
CACHE_ENABLED = True
CACHE_CAPACITY = 10000
CACHE_SIZE = 0
lineNum = 0

def parse_record(line, filename, idx):
    line = line.rstrip('\n')
    line = line.decode('ascii', 'ignore')
    if line == '':
        return None
    if line[0] == '|':
        return None
    infos = line.strip().rstrip('|').split('|')
    stat = infos[0].strip().split()
    values = infos[1:]
    if len(stat) < 2:
        stat = '|'.join(infos[0:2]).strip().split()
        values = infos[2:]
    query_name = stat[0]
    query_type = stat[1]
    values_count = int(stat[2])
    if values_count > len(values):
        for num in range(idx, idx+values_count-len(values)+1):
            temp_values = linecache.getline(filename, num)
            if temp_values[0] == '|':
                values.append(temp_values.lstrip('|').strip('\n'))
        linecache.clearcache()
    return {'query_name': query_name, 'query_type': query_type, 'values': values, 'values_count': values_count}

def parse_value(item):
    global lineNum
    temp_info = item.strip().split()
    count = int(temp_info[0])
    first_seen = temp_info[1]
    last_seen = temp_info[2]
    if temp_info[1] > temp_info[2]:
        first_seen = temp_info[2]
        last_seen = temp_info[1]
    ns_ip = temp_info[3]
    ttl = temp_info[4]
    authority = temp_info[5]
    value = temp_info[6]
    if len(temp_info) > 7:
        value = ' '.join(temp_info[6:])
    lineNum += 1
    return {'count': count, 'first_seen': first_seen, 'last_seen': last_seen, 'ns_ip': ns_ip, 'ttl': ttl, 'authority': authority, 'value': value}

def save_to_db(value, t_records):
    #print value['query_name'], ' ', value['query_type'], ' ', value['ns_ip'], ' ', value['first_seen'], ' ', value['last_seen']
    if value.has_key('_id'):
        t_records.update({'_id': value['_id']}, \
            {'$set': {'count': value['count'], 'first_seen': value['first_seen'], \
            'last_seen': value['last_seen'], 'ttl': value['ttl'], \
            'authority': value['authority']}})
    else:
        t_records.insert({'query_name': value['query_name'], 'query_type': value['query_type'], \
                'ns_ip': value['ns_ip'], 'value': value['value'], 'ttl': value['ttl'], 'count': value['count'], \
                'first_seen': value['first_seen'], 'last_seen': value['last_seen'], 'sensor': 'CERNET', \
                'authority': value['authority']})

def swap_out_cache(t_records):
    global RecordValueCache
    global last_swap_out_time
    global CACHE_SIZE
    swap_begin_time = datetime.datetime.now()
    #print 'swap: ', (swap_begin_time - last_swap_out_time).seconds

    for query_type, query_type_map in RecordValueCache.items():
        for ns_ip, ns_ip_map in query_type_map.items():
            for value, value_map in ns_ip_map.items():
                for query_name, record in value_map.items():
                    save_to_db(record, t_records)
                value_map.clear()
            ns_ip_map.clear()
        query_type_map.clear()

    RecordValueCache.clear()

    CACHE_SIZE = 0

    swap_end_time = datetime.datetime.now()
    #print '\t', (swap_end_time - swap_begin_time).seconds
    last_swap_out_time = swap_end_time

def update_cached_recordvalue(recordvalue, t_records):
    global RecordValueCache
    global CACHE_SIZE
    global CACHE_CAPACITY
    query_type = recordvalue['query_type']
    query_name = recordvalue['query_name']
    ns_ip = recordvalue['ns_ip']
    value = recordvalue['value']

    RecordValueCache[query_type][ns_ip][value][query_name] = recordvalue
    CACHE_SIZE = CACHE_SIZE + 1

    if CACHE_SIZE > CACHE_CAPACITY:
        swap_out_cache(t_records)

def find_cached_recordvalue(file_recordvalue):
    global RecordValueCache
    query_type = file_recordvalue['query_type']
    query_name = file_recordvalue['query_name']
    ns_ip = file_recordvalue['ns_ip']
    value = file_recordvalue['value']

    if not RecordValueCache.has_key(query_type):
        RecordValueCache[query_type] = {}

    if not RecordValueCache[query_type].has_key(ns_ip):
        RecordValueCache[query_type][ns_ip] = {}

    if not RecordValueCache[query_type][ns_ip].has_key(value):
        RecordValueCache[query_type][ns_ip][value] = {}

    if RecordValueCache[query_type][ns_ip][value].has_key(query_name):
        return RecordValueCache[query_type][ns_ip][value][query_name]
    else:
        return None

def find_db_recordvalue(file_recordvalue, t_records):
    result = t_records.find_one({'query_name': file_recordvalue['query_name'], \
            'query_type': file_recordvalue['query_type'], 'ns_ip': file_recordvalue['ns_ip'], \
            'value': file_recordvalue['value']}, {'_id': 1, 'query_name': 1, 'query_type': 1, \
            'ns_ip': 1, 'value': 1, 'ttl': 1, 'authority': 1, \
            'first_seen': 1, 'last_seen': 1, 'count': 1})
    return result

def update_recordvalue(file_recordvalue, t_records):
    recordvalue = None

    if CACHE_ENABLED == True:
        recordvalue = find_cached_recordvalue(file_recordvalue)

    if not recordvalue:
        recordvalue = find_db_recordvalue(file_recordvalue, t_records)

    if recordvalue:
        if recordvalue['first_seen'] > file_recordvalue['first_seen']:
            recordvalue['first_seen'] = file_recordvalue['first_seen']
        if recordvalue['last_seen'] < file_recordvalue['last_seen']:
            recordvalue['last_seen'] = file_recordvalue['last_seen']
        recordvalue['count'] = recordvalue['count'] + file_recordvalue['count']
        recordvalue['ttl'] = file_recordvalue['ttl']
    else:
        recordvalue = file_recordvalue

    if CACHE_ENABLED == True:
        update_cached_recordvalue(recordvalue, t_records)
    else:
        save_to_db(recordvalue, t_records)


#ns5.iqilu.com 1 1 17|17 1389096019 1389098461 119.164.219.2 7200 T 119.164.219.2
def parse_records(input, t_records, filename):
    i = 0
    try:
        lasttime = datetime.datetime.now()
        for line in input:
            i += 1

            file_record = parse_record(line, filename, i)
            
            if file_record is None or file_record['values_count'] == 0:
                continue

            for item in file_record['values']:
                if not item:
                    continue
                file_recordvalue = parse_value(item)
                file_recordvalue['query_name'] = file_record['query_name']
                file_recordvalue['query_type'] = file_record['query_type']
                update_recordvalue(file_recordvalue, t_records)
                
    except Exception, e:
        print traceback.format_exc()
        print 'filename:', filename, ' errorline:', i 
        os.rename(filename, filename.rstrip('.processing') + '.' + str(i) + '.error')


def store_db(filename, t_records):
    input = open(filename, 'r')
    os.rename(filename, filename + '.processing')
    parse_records(input, t_records, filename + '.processing')
    if os.path.isfile(filename + '.processing'):
        os.rename(filename + '.processing', filename + '.processed')
    input.close()
	
if __name__ == '__main__':
    pf = 'ps -ef|grep "/usr/bin/python /home/houman/script/dns_analyse.py >> /home/houman/log/process_file_list_log"'
    status, output = commands.getstatusoutput(pf)
    output_list = output.split('\n')
    if len(output_list) > 3:
        sys.exit(0)
 
    conn = MongoClient('localhost',27017)
    db = conn.dns
    #db.authenticate('passivedns','ccert@213')

    #/home/passive-dns/test_zxf
    filenames = glob.glob(DNS_DATA_DIRECTORY)
    filenames = sorted(filenames)
    lasttime = datetime.datetime.now()
    for filename in filenames[0:1]:
        print filename
        os.rename(filename, filename.replace('-',''))
        filename = filename.replace('-','')
        lineNum = float('%0.4f' %(lineNum))
        store_db(filename, db.records)
        print 'Handled records: %s. ', int(lineNum)
        curtime = datetime.datetime.now()
        seconds = float('%0.4f' %((curtime - lasttime).seconds))
        print 'Used time: %s seconds. ' %(seconds)
        if int(seconds) != 0:
            print 'Speed: %s per second.' %(float('%0.4f'%(lineNum/seconds)))
        print ''
        lasttime = curtime
    db.logout()
