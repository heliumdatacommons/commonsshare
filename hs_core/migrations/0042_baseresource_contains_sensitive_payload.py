# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hs_core', '0041_baseresource_assessment_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='baseresource',
            name='contains_sensitive_payload',
            field=models.BooleanField(default=False),
        ),
    ]
