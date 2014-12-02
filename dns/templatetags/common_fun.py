from django import template
from django.template import Context, Template, loader, resolve_variable
import time
import re
register = template.Library()


class ValuesNode(template.Node):
	def __init__(self, var_name, values, query_name, query_type, ns_ip, value):
		self.var_name = var_name
		self.values = values
		self.query_name = str(query_name)
		self.query_type = str(query_type)
		self.ns_ip = str(ns_ip)
		self.value = str(value)

	def render(self, context):
		#var_name = resolve_variable(self.var_name, context)
		values = list(resolve_variable(self.values, context))
		query_name = str(resolve_variable(self.query_name, context))
		query_type = str(resolve_variable(self.query_type, context))
		ns_ip = str(resolve_variable(self.ns_ip, context))
		value = str(resolve_variable(self.value, context))
        
        #print 'value renden:', value
        #new_values = []
        #if not ns_ip and not value:
        #    new_values = values
        #if ns_ip and not value:
        #    for item in values:
        #        if item['ns_ip'] == ns_ip:
        #            new_values.append(item)

		#if value and not ns_ip:
		#	for item in values:
		#		if item['value'] == value:
		#			new_values.append(item)
		
		#if value and ns_ip:
		#	for item in values:
		#		if item['ns_ip'] == ns_ip and item['value'] == value:
		#			new_values.append(item)
			
			
		#context[self.var_name] = new_values
		#print 'new_values:', new_values
				
		#return ''

def str_time(value):
    if value:
        return time.strftime('%Y-%m-%d %X', time.localtime(long(value)))
    return value

def handlename(value):
    return value.rstrip('.csv')

def arr_length(arr):
	return len(arr) + 1

def getId(value):
    return ''.join(value.split('.'))

def getDomain(value):
    tmpList = value.split('|')
    if len(tmpList) == 2:
        return tmpList[0]
    return value

def getType(value):
    tmpList = value.split('|')
    if len(tmpList) == 2:
        return tmpList[1]
    return value

 
def new_values(parser, token):
	try:
		tag_name, args = token.contents.split(None, 1)
	except ValueError:
		msg = '%s tag requires arguments' %(token.contents[0])
		raise template.TemplateSyntaxError(msg)
	m = re.search(r'(.*?) as (\w+)', args) 
	if m:
		choices, var_name = m.groups()
	else:
		msg = '%r tag had invalid arguments' % tag_name
		raise template.TemplateSyntaxError(msg) 
	choices = choices.strip()
	values, query_name, query_type, value, ns_ip = choices.split()
	return ValuesNode(var_name, values, query_name, query_type, ns_ip, value)
	
	
register.filter('getId',getId)
register.filter('getDomain',getDomain)
register.filter('getType',getType)
register.filter('str_time', str_time)
register.filter('handlename', handlename)
register.filter('arr_length', arr_length)
register.tag('new_values', new_values)
