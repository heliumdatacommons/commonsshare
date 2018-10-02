# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0039_remove_baseresource_doi'),
    ]

    operations = [
        migrations.AddField(
            model_name='baseresource',
            name='doi',
            field=models.CharField(help_text=b'DOI created for this resource.', max_length=1024, null=True, db_index=True, blank=True),
        ),
    ]
