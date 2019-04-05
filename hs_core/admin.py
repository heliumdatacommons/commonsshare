from django.contrib.gis import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from .models import *


class InlineResourceFiles(GenericTabularInline):
    model = ResourceFile


admin.site.register(GenericResource)
