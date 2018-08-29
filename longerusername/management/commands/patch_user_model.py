from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection


class Command(BaseCommand):
    help = "Patch default user model to increase username max length from 30 to what is defined " \
           "in MAX_USERNAME_LENGTH in settings"

    def handle(self, *args, **options):
        cursor = connection.cursor()
        sqlcmd = 'ALTER TABLE auth_user ALTER COLUMN username TYPE varchar(' + \
                 str(settings.MAX_USERNAME_LENGTH) + ');'
        cursor.execute(sqlcmd)
