# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_access_control', '0023_auto_20180423_1904'),
    ]

    operations = [
        migrations.AddField(
            model_name='groupaccess',
            name='require_dua_signoff',
            field=models.BooleanField(default=False, help_text=b'whether to require sign-off of data usage agreement before a member joins the group'),
        ),
    ]
