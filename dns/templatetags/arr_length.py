from django import template
register = template.Library()


def arr_length(values):
	return len(values) + 1


register.filter('arr_length', arr_length)
