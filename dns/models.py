from django.db import models
from mongoengine import *
# Create your models here.


class Value(EmbeddedDocument):
	ns_ip = StringField()
	value = StringField()
	first_seen = StringField()
	last_seen = StringField()
	count = IntField()
	ttl = StringField()
	sensor = StringField()
	
class Rrsets(Document):
    _id = StringField()
    query_name = StringField()
    query_type = StringField()
    value = StringField()
    ns_ip = StringField()
    first_seen = StringField()
    last_seen = StringField() 
    count = IntField()
    ttl = StringField()
    sensor = StringField() 
    meta = {"collection": "records", "indexes":["query_name","query_type","ns_ip","value","ttl"]}





class Names(Document):
    _id = StringField()
    query_name = StringField()
    query_type = StringField()
    ttl = IntField()
    type = StringField()
    status = IntField()
    meta = {'collection':'domain_names', 'indexes':[('query_name','query_type')]}


class Ns(Document):
    _id = StringField()
    ns_ip = StringField()
    meta = {'collection':'ns', 'indexes':['ns_ip']}

class NameValueNS(Document):
    _id = StringField()
    query_name = StringField()
    value = StringField()
    meta = {'collection':'name_value_ns', 'indexes':['query_name','value']}
