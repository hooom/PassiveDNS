from django.shortcuts import render
from mongoengine.django.shortcuts import get_document_or_404
from dns.models import Rrsets, Names, Ns, NameValueNS
from django.core.paginator import Paginator
#from dns.newpaginator import NewPaginator
import commands
import Queue
import os
import glob
import dgachecker
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.ticker import MultipleLocator, FuncFormatter
import numpy as np
import time
import datetime
from geoip import geolite2
import multiprocessing
from dns.commons import *


top_filter = ['com', 'co', 'edu', 'net', 'ad', 'ac', 'org', 'gc', 'sh']

# Create your views here.
def index(request):
    query_name = request.POST.get('query_name', '')
    query_type = request.POST.get('query_type', '')
    ns_ip = request.POST.get('ns_ip', '')
    value = request.POST.get('value', '')
    page = int(request.POST.get('page_number',1))
    query_list = []
    page_size = 100
    first,last = (page-1) * page_size, page * page_size
    count = 0
    # one choice
    if query_name and not ns_ip and not query_type and not value:
        query_list = Rrsets.objects(query_name__exact=query_name).all()[first:last]
        count = Rrsets.objects(query_name__exact=query_name).all().count()
    if ns_ip and not query_name and not query_type and not value:
        query_list = Rrsets.objects(ns_ip__exact=ns_ip).all()[first:last]
        count = Rrsets.objects(ns_ip__exact=ns_ip).all().count()
    if query_type and not query_name and not ns_ip and not value:
        query_list = Rrsets.objects(query_type__exact=query_type).all()[first:last]
        count = Rrsets.objects(query_type__exact=query_type).all().count()
    if value and not query_name and not ns_ip and not query_type:
        query_list = Rrsets.objects(value__exact=value).all()[first:last]
        count = Rrsets.objects(value__exact=value).all().count()

    #two choice
    #print 'query_name:', query_name, ' query_type:', query_type, ' ns_ip:', ns_ip, ' value:', value
    if query_name and query_type and not ns_ip and not value:
        query_list = Rrsets.objects(query_name__exact=query_name, query_type__exact=query_type).all()[first:last]
        count = Rrsets.objects(query_name__exact=query_name, query_type__exact=query_type).all().count()
    if query_name and ns_ip and not query_type and not value:
        query_list = Rrsets.objects(ns_ip__exact=ns_ip, query_name__exact=query_name).all()[first:last]
        count = Rrsets.objects(ns_ip__exact=ns_ip, query_name__exact=query_name).all().count()
    if ns_ip and query_type and not query_name and not value:
        query_list = Rrsets.objects(ns_ip__exact=ns_ip, query_type__exact=query_type).all()[first:last]
        count = Rrsets.objects(ns_ip__exact=ns_ip, query_type__exact=query_type).all().count()
    if value and query_name and not ns_ip and not query_type:
        query_list = Rrsets.objects(value__exact=value, query_name__exact=query_name).all()[first:last]
        count = Rrsets.objects(value__exact=value, query_name__exact=query_name).all().count()
    if value and query_type and not query_name and not ns_ip:
        query_list = Rrsets.objects(value__exact=value, query_type__exact=query_type).all()[first:last]
        count = Rrsets.objects(value__exact=value, query_type__exact=query_type).all().count()
    if value and ns_ip and not query_name and not query_type:
        query_list = Rrsets.objects(value__exact=value, ns_ip__exact=ns_ip).all()[first:last]
        count = Rrsets.objects(value__exact=value, ns_ip__exact=ns_ip).all().count()

    #three choices
    if ns_ip and query_type and query_name and not value:
        query_list = Rrsets.objects(ns_ip__exact=ns_ip, query_type__exact=query_type,query_name__exact=query_name).all()[first:last]
        count = Rrsets.objects(ns_ip__exact=ns_ip, query_type__exact=query_type,query_name__exact=query_name).all().count()
    if query_name and query_type and value and not ns_ip:
        query_list = Rrsets.objects(value__exact=value, query_type__exact=query_type,query_name__exact=query_name).all()[first:last]
        count = Rrsets.objects(value__exact=value, query_type__exact=query_type,query_name__exact=query_name).all().count()
    if query_name and value and ns_ip and not query_type:
        query_list = Rrsets.objects(value__exact=value, ns_ip__exact=ns_ip,query_name__exact=query_name).all()[first:last]
        count = Rrsets.objects(value__exact=value, ns_ip__exact=ns_ip,query_name__exact=query_name).all().count()
    if query_type and value and ns_ip and not query_name:
        query_list = Rrsets.objects(value__exact=value, ns_ip__exact=ns_ip,query_type__exact=query_type).all()[first:last]
        count = Rrsets.objects(value__exact=value, ns_ip__exact=ns_ip,query_type__exact=query_type).all().count()

    #four choices
    if ns_ip and query_type and query_name and value:
        query_list = Rrsets.objects(value__exact=value, ns_ip__exact=ns_ip,query_type__exact=query_type, query_name__exact=query_name).all()[first:last]
        count = Rrsets.objects(value__exact=value, ns_ip__exact=ns_ip, query_type__exact=query_type,query_name__exact=query_name).all().count()

    paginator = Paginator(query_list, page_size, count)
    temp_query_list = paginator.page(page)

    query_dict = {}

    for query in query_list:
        if query_dict.has_key(query['query_name'] + '|' + query['query_type']):
            query_dict[query['query_name'] + '|' + query['query_type']].append({'ns_ip':query['ns_ip'],'value':query['value'],'ttl':query['ttl'],\
                        'sensor':query['sensor'],'first_seen':query['first_seen'],'last_seen':query['last_seen'],'count':query['count']})
        else:
            query_dict[query['query_name'] + '|' + query['query_type']]=[{'ns_ip':query['ns_ip'],'value':query['value'],'ttl':query['ttl'],\
                    'sensor':query['sensor'],'first_seen':query['first_seen'],'last_seen':query['last_seen'],'count':query['count']}]

    query_list_new = []
    for key,values in query_dict.items():
        name = key.split('|')[0]
        type = key.split('|')[1]
        total = 0
        for temp_value in values:
            total = total + temp_value['count']
        query_list_new.append({'query_name':name,'query_type':type, 'total':total, 'values':values})

    #paginator = Paginator(query_list_new, page_size, count)
    #query_list_new = paginator.page(page)
    
    context = {'query_list_new': query_list_new, 'query_list':temp_query_list,'query_name':query_name,\
	 'query_type':query_type, 'ns_ip':ns_ip, 'value':value,'total':count}
    return render(request, 'index.html', context)

def domain_suspicious1(request):
    page = int(request.GET.get('page_number',1))
    query_list = []
    page_size = 1000
    first,last = (page-1) * page_size, page * page_size
   
    query_list = []
    count = 0
    ns_ip_list = Rrsets.objects(query_type__exact="5", ttl__exact="5").distinct('ns_ip')
    for ns_ip in ns_ip_list: 
        temp1_query_list = Rrsets.objects(ns_ip__exact=ns_ip,query_type__exact="1").all()[first:last] 
        temp1_count = Rrsets.objects(ns_ip__exact=ns_ip,query_type__exact="1").all().count()
        query_list += list(temp1_query_list)
        count += temp1_count


    paginator = Paginator(query_list, page_size, count)
    temp_query_list = paginator.page(page)

    query_dict = {}
    for query in query_list:
        if query_dict.has_key(query['query_name'] + '|' + query['query_type']):
            query_dict[query['query_name'] + '|' + query['query_type']].append({'ns_ip':query['ns_ip'],'value':query['value'],'ttl':query['ttl'],\
                'sensor':query['sensor'],'first_seen':query['first_seen'],'last_seen':query['last_seen'],'count':query['count']})
	else:
	    query_dict[query['query_name'] + '|' + query['query_type']]=[{'ns_ip':query['ns_ip'],'value':query['value'],'ttl':query['ttl'],\
                'sensor':query['sensor'],'first_seen':query['first_seen'],'last_seen':query['last_seen'],'count':query['count']}]

    query_list_new = []
    for key,values in query_dict.items():
        name = key.split('|')[0]
        type = key.split('|')[1]
        total = 0
        for temp_value in values:
            total = total + temp_value['count']
        query_list_new.append({'query_name':name,'query_type':type, 'total':total, 'values':values})

    context = {'query_list_new': query_list_new, 'query_list':temp_query_list, 'total':count}
    return render(request, 'domain_suspicious.html', context)
        
def domain_suspicious(request):
    page = int(request.GET.get('page_number',1))
    query_list = []
    page_size = 1000
    first,last = (page-1) * page_size, page * page_size
    
    query_list_1 = Rrsets.objects(ns_ip__exact='112.90.141.215', query_type__exact='1').all()[first:last]
    count_1 = Rrsets.objects(ns_ip__exact='112.90.141.215', query_type__exact='1').all().count()

    query_list_2 = Rrsets.objects(ns_ip__exact='54.241.0.207', query_type__exact='1').all()[first:last]
    count_2 = Rrsets.objects(ns_ip__exact='54.241.0.207', query_type__exact='1').all().count()

    query_list_3 = Rrsets.objects(ns_ip__exact='54.228.253.233', query_type__exact='1').all()[first:last]
    count_3 = Rrsets.objects(ns_ip__exact='54.228.253.233', query_type__exact='1').all().count()

    query_list = list(query_list_1) + list(query_list_2) + list(query_list_3)
    count = count_1 + count_2 + count_3

    paginator = Paginator(query_list, page_size, count)
    temp_query_list = paginator.page(page)

    query_dict = {}
    for query in query_list:
        if query_dict.has_key(query['query_name'] + '|' + query['query_type']):
    	    query_dict[query['query_name'] + '|' + query['query_type']].append({'ns_ip':query['ns_ip'],'value':query['value'],'ttl':query['ttl'],\
    		'sensor':query['sensor'],'first_seen':query['first_seen'],'last_seen':query['last_seen'],'count':query['count']})
    	else:
    	    query_dict[query['query_name'] + '|' + query['query_type']]=[{'ns_ip':query['ns_ip'],'value':query['value'],'ttl':query['ttl'],\
    		'sensor':query['sensor'],'first_seen':query['first_seen'],'last_seen':query['last_seen'],'count':query['count']}]

    query_list_new = []
    for key,values in query_dict.items():
        name = key.split('|')[0]
    	type = key.split('|')[1]
    	total = 0
    	for temp_value in values:
    	    total = total + temp_value['count']
    	query_list_new.append({'query_name':name,'query_type':type, 'total':total, 'values':values})

    context = {'query_list_new': query_list_new, 'query_list':temp_query_list, 'total':count}
    return render(request, 'domain_suspicious.html', context)

def domain_suspicious_1(request):
    page = int(request.GET.get('page_number',1))
    query_list = []
    page_size = 100
    first,last = (page-1) * page_size, page * page_size
    query_list = Rrsets.objects.filter(ttl='5')[first:last]
    count = Rrsets.objects.filter(ttl='5').count()
    paginator = Paginator(query_list, page_size, count)
    temp_query_list = paginator.page(page)

    query_dict = {}

    for query in query_list:
        if query_dict.has_key(query['query_name'] + '|' + query['query_type']):
            query_dict[query['query_name'] + '|' + query['query_type']].append({'ns_ip':query['ns_ip'],'value':query['value'],'ttl':query['ttl'],\
		'sensor':query['sensor'],'first_seen':query['first_seen'],'last_seen':query['last_seen'],'count':query['count']})
	else:
	    query_dict[query['query_name'] + '|' + query['query_type']]=[{'ns_ip':query['ns_ip'],'value':query['value'],'ttl':query['ttl'],\
            	'sensor':query['sensor'],'first_seen':query['first_seen'],'last_seen':query['last_seen'],'count':query['count']}]
    
    query_list_new = []
    for key,values in query_dict.items():
        name = key.split('|')[0]
        type = key.split('|')[1]
        total = 0
        for temp_value in values:
            total = total + temp_value['count']
        query_list_new.append({'query_name':name,'query_type':type, 'total':total, 'values':values})

    context = {'query_list_new': query_list_new, 'query_list':temp_query_list,'total':count}
    return render(request, 'domain_suspicious.html', context)

def domain_stats(request):
    #recordtype table
    recordType = [['A', '24078008', '12.36%'],\
                  ['NS', '4832837', '2.48%'], \
                  ['CNAME', '161846929', '83.05%'], \
                  ['TXT', '539692', '0.27%'], \
                  ['PTR', '3508597', '1.80%'], \
                  ['AAAA', '78481', '0.04%'], \
                  ['TOTAL', '194884544', '100%']]

    #TTL distrubute line
    ttl = [['0-10', 153889437],\
           ['10-100', 4226980],\
           ['100-1000', 9632042],\
           ['1000-10000', 10991078],\
           ['10000-100000', 15793781],\
           ['100000-1000000', 279432],\
           ['1000000-10000000', 71691], \
           ['10000000-100000000', 59], \
           ['100000000-1000000000', 44]]

    #ip map column
    ipmap = [['221.8.69.25', 947], ['64.62.224.252', 973],\
             ['184.82.227.188', 1054], ['222.216.190.69', 1322],\
             ['65.19.141.205', 1393], ['175.100.207.156', 1556], \
             ['175.100.207.155', 1705], ['222.216.190.62', 1862], \
             ['222.216.190.60', 1937], ['127.0.0.1', 2189], \
             ['122.112.2.14', 2857], ['180.76.3.43', 3095], \
             ['68.68.105.172', 3623], ['222.216.190.71', 3627], \
             ['61.155.149.87', 3932], ['65.49.2.178', 4006], \
             ['61.155.149.89', 4965], ['61.155.149.88', 4985], \
             ['222.216.190.64', 5446], ['112.125.17.103', 5712]
            ]

    #TOP 20 domain table
    topdomain = [['honpus.com', '19441898955','1','92','nxdomain'], \
                 ['sf123.org.cn', '10466096491', '1', '10', 'noerror'], \
                 ['game69.com', '4876519178', '4', '22', 'nxdomain'], \
                 ['ywool.com', '4241731600', '1', '14', 'noerror'], \
                 ['hh.cc', '3826328944', '5', '26', 'noerror'], \
                 ['taodake.com', '3540721717', '27', '19', 'noerror'], \
                 ['60sf.com', '3463506269', '3113', '28', 'serverfail'],\
                 ['94gg.com', '2774371075', '1', '59', 'noerror'], \
                 ['010udream.cn', '2404110842', '1', '10', 'noerror'], \
                 ['sxztkj.com', '2375990371', '0', '58', 'noerror'], \
                 ['oo40.com', '2369242170', '2', '94', 'serverfail'], \
                 ['game1178.com', '2279201573', '1', '29', 'noerror'], \
                 ['clai.cn', '2219639791', '1', '31', 'noerror'], \
                 ['sina.com.cn', '2215756266', '2024', '1228', 'noerror'], \
                 ['rhsyxx.cn', '1562747101', '1', '22', 'noerror'], \
                 ['iflytektj.com', '15506117551', '5727', '40', 'serverfail'], \
                 ['sf123.org', '1542264487', '1', '39', 'noerror'], \
                 ['tjldktv.com', '1479088754', '1', '18', 'noerror'], \
                 ['cqtaj.com', '1422487429', '1', '14', 'noerror'], \
                 ['qq.com', '1405224492', '24863', '1228', 'noerror']]

    #Domain dependency table
    dependency = [['1', 'dnspod.net', '364431', '66.47%', 'DNSPOD'], \
                  ['2', 'iidns.com', '81908', '14.94%','YiDong'], \
                  ['3', 'hichina.com', '34088', '6.21%','WanWang'], \
                  ['4', 'xundns.com', '17829', '3.25%','PanShiWangLuo'], \
                  ['5', 'jiasule.net', '13633', '2.49%','ZhiDaoChuangYu'], \
                  ['6', 'dns.com.cn', '11956', '2.18%','XinWang'], \
                  ['7', '360wzb.com', '10074', '1.84%', 'Qihu360'], \
                  ['8', 'domaincontrol.com', '7841', '1.43%', 'godaddy'],\
                  ['9', '01isp.com', '3284', '0.60%', 'ShiDaiWangLuo'], \
                  ['10', 'anquanbao.com', '3237', '0.59%', 'AnQuanBao']]

    
    context = {'recordType': recordType, 'ttl':ttl, 'ipmap':ipmap, 'topdomain':topdomain, 'dependency':dependency}
    return render(request, 'domain_stats.html', context)

def domain_stats1(request):
    filenames = glob.glob(r'/home/houman/PassiveDNS/static/csv/*')
    domain_names = []
    for temp in filenames:
	    domain_names.append('.'.join(temp.split('/')[-1].split('.')[0:-1]))
    
    domain_name = request.GET.get('domain_name', domain_names[0])
     
    context = {'domain_names':domain_names, 'lines_data': gen_data_domain(domain_name)}
    return render(request, 'domain_stats.html', context)

def gen_data_domain(domain_name):
    f_open = open('/home/houman/PassiveDNS/static/csv/%s.csv'%(domain_name), 'r') 
    
    all_temp_dict = {}
    a_temp_dict = {}
    ns_temp_dict = {}
    cname_temp_dict = {}
    ptr_temp_dict = {}
    txt_temp_dict = {}
    aaaa_temp_dict = {}    
    for item in f_open.readlines():
        if item.find('date') != -1:
            continue

        temp_list = item.strip(',').split(',')
        all_temp_dict[temp_list[0] + ':00:00 -0700'] = temp_list[1]
        a_temp_dict[temp_list[0] + ':00:00 -0700'] = temp_list[2]
        ns_temp_dict[temp_list[0] + ':00:00 -0700'] = temp_list[3]
        cname_temp_dict[temp_list[0] + ':00:00 -0700'] = temp_list[4]
        ptr_temp_dict[temp_list[0] + ':00:00 -0700'] = temp_list[5]
        txt_temp_dict[temp_list[0] + ':00:00 -0700'] = temp_list[6]
        aaaa_temp_dict[temp_list[0] + ':00:00 -0700'] = temp_list[7]

    line_data = []

    all_data = {}
    all_data['data'] = all_temp_dict
    all_data['name'] = 'ALL'
    
    line_data.append(all_data) 

    a_data = {}   
    a_data['data'] = a_temp_dict
    a_data['name'] = 'A'

    line_data.append(a_data)

    ns_data = {}
    ns_data['data'] = ns_temp_dict
    ns_data['name'] = 'NS'

    line_data.append(ns_data)

    cname_data = {}
    cname_data['data'] = cname_temp_dict
    cname_data['name'] = 'CNAME'

    line_data.append(cname_data)

    ptr_data = {}
    ptr_data['data'] = ptr_temp_dict
    ptr_data['name'] = 'PTR'

    line_data.append(ptr_data)

    txt_data = {}
    txt_data['data'] = txt_temp_dict
    txt_data['name'] = 'TXT'

    line_data.append(txt_data)

    aaaa_data = {}
    aaaa_data['data'] = aaaa_temp_dict
    aaaa_data['name'] = 'AAAA'
    
    line_data.append(aaaa_data)

    return line_data


def time_format_domain(s_time):
    s_date = ''.join(s_time.split()[0].strip().split('-'))
    s_hour = s_time.split()[1].strip()

    return s_date + s_hour
    
def time_format(s_time):
    s_date = ''.join(s_time.split('-')[0].strip().split('/'))
    s_hour = s_time.split('-')[1].strip().split(':')[0]
    
    return s_date + s_hour

def gen_data(query_type, start_time, end_time):
    data_dict = {}
    f_open = open('/home/houman/stats/query_type/hour/%s_stats.csv'%(query_type),'r')
    temp_dict = {}

    total = 0

    for item in f_open.readlines():
        temp_time = item.strip().split(',')[0]
        if int(temp_time) < int(time_format(start_time)):
            continue
        if int(temp_time) > int(time_format(end_time)):
            break
        count = int(item.strip().split(',')[1])
        total += count
        temp_dict[temp_time[0:4] + '-' + temp_time[4:6] + '-' + temp_time[6:8] + ' ' + temp_time[8:10]+':00:00 -0700'] = count
        
    data_dict['data'] = temp_dict
    data_dict['name'] = query_type.upper()
    
    pic_data = {}
    pic_data['lines']  = data_dict
    pic_data['column'] = [query_type.upper(), total]
    f_open.close()
    return pic_data

def gen_data_domain(start_time, end_time, type):
    print 'get domain start:', time.strftime("%Y-%m-%d %H:%M:%S")
    data_dict = {}
    count_data_list = []
    subdomain_data_list = []
    f_open = None
    if type == '1':
        f_open = open('/home/houman/stats/domain/domain_stats_a.csv','r')
    if type == '2':
        f_open = open('/home/houman/stats/domain/domain_stats_ns.csv','r')
    if type == '5':
        f_open = open('/home/houman/stats/domain/domain_stats_cname.csv','r')
    if type == '12':
        f_open = open('/home/houman/stats/domain/domain_stats_ptr.csv','r')
    if type == '16':
        f_open = open('/home/houman/stats/domain/domain_stats_txt.csv','r')
    if type == '28':
        f_open = open('/home/houman/stats/domain/domain_stats_aaaa.csv','r')
    
    temp_dict = {}
    for item in f_open:
        (temp_time, domain, response_count_str, subdomain_count_str) = item.strip().split(',')

        if int(temp_time) < int(time_format(start_time)):
            continue
        if int(temp_time) > int(time_format(end_time)):
            break
        
        if not temp_dict.has_key(domain):
            temp_dict[domain] = {}
            temp_dict[domain]['count'] = 0
            temp_dict[domain]['subdomain'] = 0

        temp_dict[domain]['count'] += int(response_count_str)
        if temp_dict[domain]['subdomain']< int(subdomain_count_str):
            temp_dict[domain]['subdomain'] = int(subdomain_count_str)

    f_open.close()
    number = 1
    for d1, x1 in sorted(temp_dict.items(), lambda x,y: cmp(x[1]['count'],y[1]['count']), reverse=True):
        if number > 20:
            break
        for d2, x2 in x1.items():
            if d2 == 'count':
                count_data_list.append([d1, x2])   
            if d2 == 'subdomain':
                subdomain_data_list.append([d1, x2])
        number += 1
    
    data_dict['count'] = count_data_list
    data_dict['subdomain'] = subdomain_data_list
    print 'get domain data end:',time.strftime("%Y-%m-%d %H:%M:%S")
    return data_dict
    
   
def domain_detail(request):
    start_time = time_format(request.POST.get('start_time','2014/03/01 - 00:00'))
    end_time = time_format(request.POST.get('end_time', '2014/03/07 - 00:00'))
    data_dict_a = {}

    files = commands.getoutput("cd /home/houman/txt/;find *.processed |awk -F'.' '$1 >= \"%s\" && $1 <= \"%s\" {print $0}'"\
                                                 %(start_time, end_time))
    file_list = files.split('\n')
    print file_list
    second_domains_a = request.POST.get("second_domains_a", []) 
   
    second_domains_a = second_domains_a.replace('[','') 
    second_domains_a = second_domains_a.replace(']','')
    second_domains_a = second_domains_a.replace('\'','')
    second_domains_a = second_domains_a.replace('"','')
    second_domains_a = second_domains_a.split(',')
    data_dict_a = getDataFromFile(file_list, '1', second_domains_a)
    context = {'domain_dict':data_dict_a}    
    return render(request, 'domain_detail.html', context)

def query_type_stats(request):
    default_start_time = get_default_start_time()
    default_end_time = get_default_end_time()
    start_time = request.POST.get('start_time','2014/03/01 - 00:00')
    end_time = request.POST.get('end_time', '2014/03/01 - 00:00')
    

    hour_data = []
    total_data = []
    print 'total count start:', time.strftime("%Y-%m-%d %H:%M:%S")
    #a_data = gen_data('a', start_time, end_time) 
    #ns_data = gen_data('ns', start_time, end_time)
    #cname_data = gen_data('cname', start_time, end_time)
    #txt_data = gen_data('txt', start_time, end_time)
    #ptr_data = gen_data('ptr', start_time, end_time)
    #aaaa_data = gen_data('aaaa', start_time, end_time)
    pool_type_stats = multiprocessing.Pool(processes=8)
    resultOne = []
    resultOne.append(pool_type_stats.apply_async(gen_data,('a',start_time,end_time,)))
    resultOne.append(pool_type_stats.apply_async(gen_data,('ns',start_time,end_time,)))
    resultOne.append(pool_type_stats.apply_async(gen_data,('cname',start_time,end_time,)))
    resultOne.append(pool_type_stats.apply_async(gen_data,('txt',start_time,end_time,)))
    resultOne.append(pool_type_stats.apply_async(gen_data,('ptr',start_time,end_time,)))
    resultOne.append(pool_type_stats.apply_async(gen_data,('aaaa',start_time,end_time,)))
    pool_type_stats.close()
    pool_type_stats.join()
    
    a_data = resultOne[0].get()
    ns_data = resultOne[1].get()
    cname_data = resultOne[2].get()
    txt_data = resultOne[3].get()
    ptr_data = resultOne[4].get()
    aaaa_data = resultOne[5].get()
    print 'total count end:', time.strftime("%Y-%m-%d %H:%M:%S")

    hour_data.append(a_data['lines'])
    hour_data.append(ns_data['lines'])
    hour_data.append(cname_data['lines'])
    hour_data.append(ptr_data['lines'])
    hour_data.append(txt_data['lines'])
    hour_data.append(aaaa_data['lines'])

    total_data.append(a_data['column'])
    total_data.append(ns_data['column'])
    total_data.append(cname_data['column'])
    total_data.append(ptr_data['column'])
    total_data.append(txt_data['column'])
    total_data.append(aaaa_data['column'])

    print 'total start:', time.strftime("%Y-%m-%d %H:%M:%S")
    #data_dict_a = gen_data_domain(start_time, end_time, '1')
    #data_dict_ns = gen_data_domain(start_time, end_time, '2')
    #data_dict_cname = gen_data_domain(start_time, end_time, '5')
    #data_dict_ptr = gen_data_domain(start_time, end_time, '12')
    #data_dict_txt = gen_data_domain(start_time, end_time, '16')
    #data_dict_aaaa = gen_data_domain(start_time, end_time, '28')
    pool_domain_stats = multiprocessing.Pool(processes=8)
    resultTwo = []
    resultTwo.append(pool_domain_stats.apply_async(gen_data_domain,(start_time,end_time,'1',)))
    resultTwo.append(pool_domain_stats.apply_async(gen_data_domain,(start_time,end_time,'2',)))
    resultTwo.append(pool_domain_stats.apply_async(gen_data_domain,(start_time,end_time,'5',)))
    resultTwo.append(pool_domain_stats.apply_async(gen_data_domain,(start_time,end_time,'12',)))
    resultTwo.append(pool_domain_stats.apply_async(gen_data_domain,(start_time,end_time,'16',)))
    resultTwo.append(pool_domain_stats.apply_async(gen_data_domain,(start_time,end_time,'28',)))
    pool_domain_stats.close()
    pool_domain_stats.join()
    data_dict_a = resultTwo[0].get()
    data_dict_ns = resultTwo[1].get()
    data_dict_cname = resultTwo[2].get()
    data_dict_ptr = resultTwo[3].get()
    data_dict_txt = resultTwo[4].get()
    data_dict_aaaa = resultTwo[5].get()
    print 'total end:', time.strftime("%Y-%m-%d %H:%M:%S")

    second_domains_a = []
    for tmp in data_dict_a['subdomain']:
        second_domains_a.append(tmp[0])
    
    second_domains_ns = []
    for tmp in data_dict_ns['subdomain']:
        second_domains_ns.append(tmp[0])

    second_domains_cname = []
    for tmp in data_dict_cname['subdomain']:
        second_domains_cname.append(tmp[0])

    second_domains_ptr = []
    for tmp in data_dict_ptr['subdomain']:
        second_domains_ptr.append(tmp[0])

    second_domains_txt = []
    for tmp in data_dict_txt['subdomain']:
        second_domains_txt.append(tmp[0])
    
    second_domains_aaaa = []
    for tmp in data_dict_aaaa['subdomain']:
        second_domains_aaaa.append(tmp[0])


    context = {'lines_data':hour_data,'column_data':total_data,\
             'column_data_count_a':data_dict_a['count'],\
            'column_data_subdomain_a':data_dict_a['subdomain'],\
            'column_data_count_ns':data_dict_ns['count'],\
            'column_data_subdomain_ns':data_dict_ns['subdomain'],\
            'column_data_count_cname':data_dict_cname['count'],\
            'column_data_subdomain_cname':data_dict_cname['subdomain'],\
            'column_data_count_ptr':data_dict_ptr['count'],\
            'column_data_subdomain_ptr':data_dict_ptr['subdomain'],\
            'column_data_count_txt':data_dict_txt['count'],\
            'column_data_subdomain_txt':data_dict_txt['subdomain'],\
            'column_data_count_aaaa':data_dict_aaaa['count'],\
            'column_data_subdomain_aaaa':data_dict_aaaa['subdomain'],\
            'second_domains_a':second_domains_a,\
            'second_domains_ns':second_domains_ns,\
            'second_domains_cname':second_domains_cname,\
            'second_domains_ptr':second_domains_ptr,\
            'second_domains_txt':second_domains_txt,\
            'second_domains_aaaa':second_domains_aaaa,\
            'start_time':start_time, 'end_time':end_time}
    return render(request, 'query_type_stats.html', context)

def query_type_stats_1(request):
    type = request.POST.get('type','hour')

    default_start_time = get_default_start_time
    default_end_time = get_default_end_time

    start_time = request.POST.get('start_time',default_start_time)
    end_time = request.POST.get('end_time', default_end_time)

    if not check_time_exist(start_time, end_time):
        return render(request, 'query_type_stats.html', {})
    else:
        img_path = gen_pic(type, start_time, end_time)
        context = {'img_path':img_path}                                                                                
        return render(request, 'query_type_stats.html', context)      

def get_default_start_time():
    return time.strftime('%Y/%m/%d-%H:%M',time.localtime(time.time()))    

def get_default_end_time():
    return datetime.datetime.fromtimestamp(time.time()-7*24*3600).strftime("%Y/%m/%d-%H:%M")

def check_time_exist(start_time, end_time):
    if start_time != '' and end_time != '':
        start_exist = commands.getoutput("grep '%s' /home/houman/stats/query_type/hour/a_stats.csv" %(start_time))
        end_exist = commands.getoutput("grep '%s' /home/houman/stats/query_type/hour/a_stats.csv" %(end_time))
        print 'start_exist:',start_exist
        print 'end_exist:', end_exist
        print 'start_exist and end_exist:',start_exist and end_exist
        return start_exist != '' and end_exist 
    else:
        print 'start_time and end_time:',start_time and end_time
        return start_time and end_time  

def read_file(type, record_type):
    return open('/home/houman/stats/query_type/%s/%s_stats.csv'%(type, record_type), 'r')    


def get_time_serial(t, type, num):
    if type == 'hour':
        if num % 72 == 0:
            t.append(item.strip().split(",")[0][0:4]+'-'+item.strip().split(",")[0][4:6]\
                         +'-'+item.strip().split(",")[0][6:8]+' '+item.strip().split(",")[0][8:10]\
                         +':00')
    elif type == 'day':
        if num % 10 == 0:
            t.append(item.strip().split(",")[0][0:4]+'-'+item.strip().split(",")[0][4:6]\
                +'-'+item.strip().split(",")[0][6:8])
    else:
        t.append(item.strip().split(",")[0][0:4]+'-'+item.strip().split(",")[0][4:6])
        

def gen_pic(type, start_time, end_time):

    fig = pl.figure(figsize=(10,8)) 

    data_count = 0
    if type == 'hour':
        data_count = 1 + int(commands.getoutput("grep -n '%s' /home/houman/stats/query_type/hour/a_stats.csv|awk -F: '{print $1}'"\
                %(end_time))) - int(commands.getoutput("grep -n '%s' /home/houman/stats/query_type/hour/a_stats.csv|awk -F: '{print $1}'\
                "%(start_time)))
    elif type == 'day':
        data_count = 1 + int(commands.getoutput("grep -n '%s' /home/houman/stats/query_type/day/a_stats.csv|awk -F: '{print $1}'"\
                %(end_time))) - int(commands.getoutput("grep -n '%s' /home/houman/stats/query_type/day/a_stats.csv|awk -F: '{print $1}'\
                 "%(start_time)))
    else:
        data_count = 1 + int(commands.getoutput("grep -n '%s' /home/houman/stats/query_type/month/a_stats.csv|awk -F: '{print $1}'"\
                 %(end_time))) - int(commands.getoutput("grep -n '%s' /home/houman/stats/query_type/month/a_stats.csv|awk -F: '\
                    {print $1}'"%(start_time)))

    x = np.arange(0, data_count, 1)
    a = []
    ns = []
    cname = []
    ptr = []
    txt = []
    aaaa = []
    t = []
    
    a_f = read_file(type, 'a')
    ns_f = read_file(type, 'ns')
    cname_f = read_file(type, 'cname')
    ptr_f = read_file(type, 'ptr')
    txt_f = read_file(type, 'txt')
    aaaa_f = read_file(type, 'aaaa')

    num=0
    for item in a_f.readlines():
        a.append(int(item.strip().split(",")[1]))
  
        get_time_serial(t,type, num)
        num += 1
    a_f.close()
    pl.plot(x, a, label='A')
    
    for item in ns_f.readlines():
        ns.append(int(item.strip().split(",")[1]))
    ns_f.close()
    pl.plot(x, ns, label='NS')

    for item in cname_f.readlines():
        cname.append(int(item.strip().split(",")[1]))
    cname_f.close()
    pl.plot(x, cname, label='CNAME')

    for item in ptr_f.readlines():
        ptr.append(int(item.strip().split(",")[1]))
    ptr_f.close()
    pl.plot(x, ptr, label='PTR')

    for item in txt_f.readlines():
        txt.append(int(item.strip().split(",")[1]))
    txt_f.close()
    pl.plot(x, txt, label='TXT')

    for item in aaaa_f.readlines():
        aaaa.append(int(item.strip().split(",")[1]))
    aaaa_f.close()
    pl.plot(x, aaaa, label='AAAA')
        

    ax = pl.gca()
    temp = []
    temp.append(np.max(a))
    temp.append(np.max(ns))
    temp.append(np.max(cname))
    temp.append(np.max(ptr))
    temp.append(np.max(txt))
    temp.append(np.max(aaaa))
    pl.ylim(0,np.max(temp))
    pl.xlim(0, np.max(x))
    pl.subplots_adjust(bottom = 0.15)

    pl.grid(True) 
    ax.xaxis.set_major_locator( MultipleLocator(80) )
    ax.yaxis.set_major_locator( MultipleLocator(100000000) )
    
    locs,labels = pl.xticks()
    pl.xticks(locs, t)

    pl.ylabel("Response Number(yi)")
    #pl.title("Record Type Response Number Statistic")

    pl.legend()
    fig.autofmt_xdate()
    if os.path.exists("/home/houman/PassiveDNS/static/img/number_stats.png"):
        os.remove("/home/houman/PassiveDNS/static/img/number_stats.png")
    pl.savefig("/home/houman/PassiveDNS/static/img/number_stats.png")

    return '/static/img/number_stats.png'


def black_list(request):
    pass

def ns_list(request):
    page = int(request.GET.get("page",1))
    page_size = 300
    first,last = (page-1) * page_size, page * page_size
    temp_ns_list = Ns.objects.order_by('ns_ip')[first:last]
    count = Ns.objects.all().count()
    
    locations = []
    
    for ip in temp_ns_list:    
        match = geolite2.lookup(ip['ns_ip'])
        latitude = 0
        longitude = 0
        if match and match.location:
            (latitude, longitude) = match.location
        
        temp_dict = {}
        temp_dict['latitude'] = latitude
        temp_dict['longitude'] = longitude
        temp_dict['ip'] = ip['ns_ip']
        locations.append(temp_dict)

    paginator = Paginator(temp_ns_list, page_size, count)
    ns_list = paginator.page(page)
    context = {'ns_list': ns_list,'locations':locations, 'total': count}
    return render(request, 'ns_list.html', context)



def domain_list(request):
    time1 = time.time()
    page = int(request.GET.get("page",1))
    page_size = 100
    first,last = (page-1) * page_size, page * page_size
    temp_domain_list = Names.objects.order_by('-total')[first:last]
    time2 = time.time()
    print 'get 100 data:', time2 - time1
    count = Names.objects.all().count()
    time3 = time.time()
    print 'get count:',time3 - time2
    
    
    paginator = Paginator(temp_domain_list, page_size, count)
    time4 = time.time()
    print 'get paginator:', time4 - time3
    domain_list = paginator.page(page)
    time5 = time.time()
    print 'get domain list :', time5 - time4
    context = {'domain_list': domain_list, 'total':count}
    return render(request, 'domain_list.html', context)

def get_ns_list(query_name):
    ns_list = Rrsets.objects(query_name__exact=query_name,query_type__exact='2').only('values.value')
    if len(ns_list) > 0:
        return ns_list[0].values
    else:
        return []

def ns_dependence(query_name, ns_store):
    if query_name == '.' or query_name == '':
        return ns_store
    ns_list = get_ns_list(query_name)


    if len(ns_list) > 0:
        ns_store.append('#')

    if len(ns_list) == 0:
        ns_dependence('.'.join(query_name.split('.')[1:]), ns_store)

    for ns in ns_list:
        if not ns.value in ns_store:
            ns_store.append(ns.value)
            if query_name in ns.value:
                if '.' in query_name:
                    ns_dependence('.'.join(query_name.split('.')[1:]), ns_store)
                else:
                    ns_dependence('.', ns_store)
            else:
                if '.' in ns.value:
                    ns_dependence('.'.join(ns.value.split('.')[1:]), ns_store)
                else:
                    ns_dependence('.', ns_store)


def dependence(query_name):
    ns_list = get_ns_list(query_name)
    ns_store = []
    for ns in ns_list:
        if not ns.value in ns_store:
            ns_store.append(ns.value)
    return ns_store


def get_second_domain(query_name):
    query_name_list = query_name.split('.')
    second_domain = query_name
    if len(query_name_list) > 2:
        if query_name_list[-2] in top_filter:
            if len(query_name_list) > 3:
                second_domain = '.'.join(query_name_list[-3:])
        else:
            second_domain = '.'.join(query_name_list[-2:])
    return second_domain
        
            

def domain_dependence(request):
    query_name = request.POST.get("query_name", "")
    if os.path.exists("/home/houman/PassiveDNS/static/img/dependency.png"):
        os.remove("/home/houman/PassiveDNS/static/img/dependency.png")
    if os.path.exists("/home/houman/PassiveDNS/static/img/dependency.dot"):
        os.remove("/home/houman/PassiveDNS/static/img/dependency.dot")
    
    dependence = 0
    if query_name:
        lines = {}
        visited = {}
        f_open = open("/home/houman/PassiveDNS/static/img/dependency.dot", "a")
        f_open.write("digraph dependency{\r\n")
        second_domain = get_second_domain(query_name)
        domain_queue = Queue.Queue()
        domain_queue.put(second_domain)
        while domain_queue.qsize() > 0:
            tmp_domain = domain_queue.get()
            visited[tmp_domain] = True
            tmp_ns_set = NameValueNS.objects(query_name__exact=tmp_domain).distinct('value')
            for tmp in tmp_ns_set:
                str_list = tmp.split('.')
                if len(str_list) >= 2:
                    tmp = '.'.join(str_list[1:])
                if tmp == tmp_domain:
                    continue
                if not visited.has_key(tmp):
                    domain_queue.put(tmp)
                if not lines.has_key('"%s" -> "%s";'%(tmp_domain, tmp)):
                    dependence += 1
                    lines['"%s" -> "%s";'%(tmp_domain, tmp)] = 1
                    f_open.write('"%s" -> "%s";\r\n'%(tmp_domain, tmp))
        f_open.close()
    
    context = {'query_name':query_name}
    if dependence > 0: 
        commands.getstatusoutput('dot /home/houman/PassiveDNS/static/img/dependency.dot -T png -o\
                         /home/houman/PassiveDNS/static/img/dependency.png')   
        context = {'domain_dependence':'/static/img/dependency.png', 'query_name':query_name}
    return render(request, 'domain_dependence.html', context)
    
def domain_dependence2(request):
    query_name = request.POST.get("query_name", "")
    if os.path.exists("/home/houman/PassiveDNS/static/img/dependency.png"):
       os.remove("/home/houman/PassiveDNS/static/img/dependency.png") 
    nodes_list = []
    edges_list = []
    visited = {}
    if query_name:
        second_domain = get_second_domain(query_name)
        domain_queue = Queue.Queue()
        G = nx.DiGraph()
        G.clear()
        domain_queue.put(second_domain)

        #graph foreach
        while domain_queue.qsize() > 0:
            tmp_domain = domain_queue.get()
            print tmp_domain
            G.add_node(tmp_domain)
            visited[tmp_domain] = True
            tmp_ns_set = NameValueNS.objects(query_name__exact=tmp_domain).distinct('value')
            for tmp in tmp_ns_set:
                if len(tmp.split('.')) > 2:
                    tmp = '.'.join(tmp.split('.')[1:])
                if tmp == tmp_domain:
                    continue
                if not visited.has_key(tmp):
                    domain_queue.put(tmp)
                G.add_edge(tmp_domain, tmp)

            
        
        pos = nx.shell_layout(G)
        nx.draw_networkx_nodes(G, pos)
        nx.draw_networkx_edges(G, pos)
        nx.draw_networkx_labels(G, pos, font_size=10)
        plt.axis('off')
        nodes_list = G.nodes()
        edges_list = G.edges()
        plt.savefig("/home/houman/PassiveDNS/static/img/dependency.png")
        plt.clf()
    context = {'domain_dependence':'/static/img/dependency.png', 'nodes':nodes_list, 'edges':edges_list}
    return render(request, 'domain_dependence.html', context)



def dga_detection(request):
    page = int(request.GET.get('page',1))
    page_size = 1000
    first,last = (page-1) * page_size, page * page_size
    queryname_list = Names.objects(type__exact='anomaly',query_type__exact='1', status__exists=True).all()[first:last]
    count = Names.objects(type__exact='anomaly',query_type__exact='1', status__exists=True).all().count()

    paginator = Paginator(queryname_list, page_size, count)
    queryname_list = paginator.page(page)

    context = {'query_list': queryname_list, 'total':count}
    return render(request, 'domain_dga.html', context)


       



def dga_check(request):
    domain = request.GET.get("domain", "")
    dga_result = dgachecker.check(domain)
    context = {'domain': domain, 'dga_result': dga_result}
    return render(request, 'dga_check.html', context)
