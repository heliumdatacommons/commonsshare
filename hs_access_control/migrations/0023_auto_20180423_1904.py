# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_access_control', '0022_resourceaccess_require_download_agreement'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groupaccess',
            name='shareable',
            field=models.BooleanField(default=False, help_text=b'whether group can be shared by non-owners', editable=False),
        ),
        migrations.AlterField(
            model_name='resourceaccess',
            name='shareable',
            field=models.BooleanField(default=False, help_text=b'whether resource can be shared by non-owners'),
        ),
    ]
