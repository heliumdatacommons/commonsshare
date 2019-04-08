from django.contrib.gis import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.contenttypes.admin import GenericTabularInline
from .models import *


class InlineResourceFiles(GenericTabularInline):
    model = ResourceFile

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(GenericResource)
