"""
Globus Auth backend that authenticates user created using info returned from oauth service, docs at:
    https://docs.globus.org/api/auth and https://github.com/heliumdatacommons/auth_microservice/wiki/API-and-Use
"""

import requests
import hashlib

from json import loads
from rest_framework import status

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.conf import settings

from hs_core.hydroshare.users import create_account


class APIKey:
    def authenticate(self, request):
        username = request.user.username
        user = User.objects.get(username=username)
        key_val = request.POST.get('apikey', '')
        url = '{}apikey/verify'.format(settings.SERVICE_SERVER_URL)
        auth_header_str = 'Basic {}'.format(settings.OAUTH_APP_KEY)
        response = requests.get(url,
                                params={'username': username,
                                        "key": key_val},
                                headers={'Authorization': auth_header_str},
                                verify=False)
        if response.status_code != status.HTTP_200_OK:
            return None
        else:
            return user


    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
