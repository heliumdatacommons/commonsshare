from django.conf.urls import patterns, url
from globus_data_reg_app import views

urlpatterns = patterns('',
    url(r'^store/$',views.store, name='globus_store'),
    url(r'^register/$',views.register, name='globus_register'),
 )
