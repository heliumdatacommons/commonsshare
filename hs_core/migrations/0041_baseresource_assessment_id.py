# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0040_baseresource_doi'),
    ]

    operations = [
        migrations.AddField(
            model_name='baseresource',
            name='assessment_id',
            field=models.PositiveIntegerField(null=True, blank=True),
        ),
    ]
