# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('theme', '0008_auto_20170622_2141'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='create_irods_user_account',
        ),
    ]
