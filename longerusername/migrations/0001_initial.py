# encoding: utf-8
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations

class Migration(migrations.Migration):

    operations = [
        migrations.RunSQL('ALTER TABLE auth_user ALTER COLUMN username TYPE varchar(' +
                          str(settings.MAX_USERNAME_LENGTH) + ')')
    ]
