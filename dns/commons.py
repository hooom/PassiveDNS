import time
import commands
import sys
import requests
import glob
import multiprocessing

toplevel = ['com', 'co', 'edu', 'net', 'ad', 'ac', 'org', 'gc', 'sh', 'ne']
def isICP(domain):
    str_list = domain.split('.')
    q = domain
    if(len(str_list)) > 2:
        if str_list[-2] in toplevel:
            q = '.'.join(str_list[-3:])
        else:
            q = '.'.join(str_list[-2:])
    api = 'http://api.apidatas.com/beian/%s' %(q)
    api1 = 'http://api.befen.net/icp.php?domain=%s' %(q)
    r = requests.get(api1)
    print r
    dict = r.json()
    if dict.has_key('status'):
        if dict['status'] == '1' and dict.has_key('beianhao'):
            return dict['beianhao']
    return None

def websiteStatus(domain):
    result = commands.getoutput("nmap -sT -p80 %s | grep open" %(domain))
    if result.split('\n')[-1].find('open') != -1:
        return "UP"
    else:
        return "DOWN"

def containSecondDomain(second_domain_list, domain):
    for tmp in second_domain_list:
        print tmp,' ', domain
        if tmp in domain:
            return tmp
    return None


def getFirstLastSeen(recordList):
    firstLast = [0, 0]
    for record in recordList:
        tmpList = record.strip().split()
        if len(tmpList) == 7:
            if firstLast[0]:
                if firstLast[0] > int(tmpList[1]):
                    firstLast[0] = tmpList[1]
            else:
                firstLast[0] = tmpList[1]

            if firstLast[1]:
                if firstLast[1] < int(tmpList[2]):
                    firstLast[1] = tmpList[2]
            else:
                firstLast[1] = tmpList[2]
    return firstLast
            

def getDataDict(data_dict, second_domain, icp, domain, record, values):
  
    firstLast = getFirstLastSeen(values)
    type =record.strip().split()[1]
    count = int(record.strip().split()[3])
    if not data_dict.has_key(second_domain + '|' + type):
        data_dict[second_domain + '|' + type] = {}

    if data_dict.has_key(second_domain + '|' + type):
        data_dict[second_domain + '|' + type]["ICP"] = icp
        
    if not data_dict[second_domain + '|' + type].has_key(domain):
        data_dict[second_domain + '|' + type][domain] = {}

    if data_dict[second_domain + '|' + type].has_key(domain):
        if not data_dict[second_domain + '|' + type][domain].has_key("first") or \
                    data_dict[second_domain + '|' + type][domain]["first"] > firstLast[0]:
            data_dict[second_domain + '|' + type][domain]["first"] = firstLast[0]
        if not data_dict[second_domain + '|' + type][domain].has_key("last") or \
                    data_dict[second_domain + '|' + type][domain]["last"] < firstLast[1]:
            data_dict[second_domain + '|' + type][domain]["last"] = firstLast[1]
        if type == '1':
            #data_dict[second_domain + '|' + type][domain]["status"] = websiteStatus(domain)
            data_dict[second_domain + '|' + type][domain]["status"] = -1
        else:
            data_dict[second_domain + '|' + type][domain]["status"] = -1

        if data_dict[second_domain + '|' + type][domain].has_key("count"):
            data_dict[second_domain + '|' + type][domain]["count"] += count
        else:
            data_dict[second_domain + '|' + type][domain]["count"] = count

    #return data_dict
                


def getDataFromFile(files, type, second_domain_list):
    data_dict = {}
    for second_domain in second_domain_list:
        second_domain = second_domain.strip()
        lines = []
        for file in files:
            result = commands.getoutput("cd /home/houman/txt/;sed -n \'/%s %s /p\' %s " %(second_domain, type, file))
            lines += result.split('\n')
        #print 'second_domain:', second_domain
        #icp = isICP(second_domain)
        icp = None
        for line in lines:
            if len(line.split('|')) < 2:
                continue
            record = line.split('|')[0]
            values = line.split('|')[1:]
            domain = record.strip().split()[0]
            if len(domain) > len(second_domain) and domain[-(len(second_domain)+1)] != '.':
                continue
            getDataDict(data_dict, second_domain, icp, domain, record, values)
    return data_dict
