from django.conf.urls import patterns, url
from dns import views


urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^domain_stats/$', views.domain_stats, name='domain_stats'),
    url(r'^domain_detail/$', views.domain_detail, name="domain_detail"),
    url(r'^query_type_stats/$', views.query_type_stats, name='query_type_stats'),
    url(r'^ns_list/$', views.ns_list, name='ns_list'),
    url(r'^black_list/$', views.black_list, name='black_list'),
    url(r'domain_suspicious/', views.domain_suspicious, name='domain_suspicious'),
    url(r'^domain_list/$', views.domain_list, name='domain_list'),
    url(r'^domain_dependence/$', views.domain_dependence, name='domain_dependence'),
    url(r'^dga_check/$', views.dga_check, name='dga_check'),
    #url(r'^dga_detection/$', views.domain_suspicious, name="domain_suspicious"),
    url(r'^dga_detection/$', views.dga_detection, name="dga_detection"),
)
