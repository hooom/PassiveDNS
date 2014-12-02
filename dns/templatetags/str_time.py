from django import template
import time
register = template.Library()


def str_time(value):
	return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(float(value)))


register.filter('str_time', str_time)
