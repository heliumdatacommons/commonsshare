from django.conf.urls import patterns, url
from hs_dos_api import views

urlpatterns = patterns(
    '',
    url(r'^dataobjects/$', views.resource_dos_api.DataObjectList.as_view(), name='list_data_objects'),
    url(r'^dataobjects/(?P<pk>[0-9a-f-]+)/$', views.resource_dos_api.DataObjectGet.as_view(), name='get_data_object'),
)
