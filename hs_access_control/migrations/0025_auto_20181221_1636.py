# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_access_control', '0024_groupaccess_require_dua_signoff'),
    ]

    operations = [
        migrations.AddField(
            model_name='groupaccess',
            name='dua_url',
            field=models.URLField(null=True, verbose_name=b'Data Use Agreement URL', blank=True),
        ),
        migrations.AddField(
            model_name='groupmembershiprequest',
            name='dua_signed',
            field=models.BooleanField(default=False),
        ),
    ]
