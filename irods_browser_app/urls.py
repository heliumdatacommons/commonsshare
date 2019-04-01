from django.conf.urls import url
from irods_browser_app import views

urlpatterns = [
    url(r'^store/$',views.store, name='irods_store'),
    url(r'^upload/$',views.upload, name='irods_upload'),
    url(r'^upload_add/$',views.upload_add, name='irods_upload_add'),
    url(r'^get_openid_token/$', views.get_openid_token, name='get_openid_token'),
]