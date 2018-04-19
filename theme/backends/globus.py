"""
Globus Auth backend that authenticates user created using info returned from oauth service, docs at:
    https://docs.globus.org/api/auth and https://github.com/heliumdatacommons/auth_microservice/wiki/API-and-Use
"""

import requests

from json import loads
from rest_framework import status

from django.contrib.auth.models import User

from hs_core.hydroshare.users import create_account


class GlobusOAuth2:
    def authenticate(self, request, username=None, access_token=None, first_name=None, last_name=None):
        AUTH_URL = 'https://auth.globus.org/v2/oauth2/userinfo'
        if not access_token or not username:
            return None

        response = requests.get(AUTH_URL,
                                headers={'Authorization': 'Bearer ' + access_token})

        if response.status_code != status.HTTP_200_OK:
            return None

        return_data = loads(response.content)
        preferred_username = return_data['preferred_username']
        if username == preferred_username:
            try:
                user = User.objects.get(username=username)
                return user
            except User.DoesNotExist:
                user = create_account(email=username, username=username, first_name=first_name, last_name=last_name,
                                      superuser=False, active=True)
                return user
        else:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
