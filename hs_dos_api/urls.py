from django.conf.urls import patterns, url
from hs_dos_api import views

urlpatterns = patterns(
    '',
    url(r'^databundles/$', views.get_databundle_list, name='get_databundle_list'),
    url(r'^databundle/$', views.create_databundle, name='create_databundle'),
    url(r'^databundle/(?P<pk>[0-9a-f-]+)/$', views.get_update_delete_databundle, name='get_update_delete_databundle'),
    url(r'^databundle/(?P<pk>[0-9a-f-]+)/versions/$', views.get_databundle_versions, name='get_databundle_versions'),

    # url(r'^dataobject/$', views.create_dataobject, name='create_dataobject'),
    # url(r'^dataobject/(?P<pk>[0-9a-f-]+)/$', core_views.resource_rest_api.ResourceFileListCreate.as_view(), name='list_create_resource_file'),
)
