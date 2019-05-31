from django.conf.urls import url
from django_irods.views import rest_download, download

urlpatterns = [
    # for download request from resource landing page
    url(r'^download/(?P<path>.*)$', download, name='django_irods_download'),
    # for download request from REST API
    url(r'^rest_download/(?P<path>.*)$', rest_download,
        name='rest_download'),
]
