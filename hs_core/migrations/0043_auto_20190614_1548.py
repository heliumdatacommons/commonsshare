# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-06-14 15:48
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0042_baseresource_contains_sensitive_payload'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='baseresource',
            name='resource_federation_path',
        ),
        migrations.RemoveField(
            model_name='resourcefile',
            name='fed_resource_file',
        ),
    ]
