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


class GlobusOAuth2:
    def authenticate(self, request, username=None, access_token=None, first_name=None, last_name=None, uid=None):
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
            auth_header_str = 'Basic {}'.format(settings.DATA_REG_API_KEY)
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                user = create_account(email=username, username=username, first_name=first_name, last_name=last_name,
                                      superuser=False, active=True)
                # create corresponding iRODS account with same username via OAuth if not exist already
                url = '{}registration/create_account?username={}&zone={}&auth_name={}'.format(
                    settings.DATA_REG_SERVICE_SERVER_URL, username, settings.IRODS_ZONE, uid)
                response = requests.get(url,
                                        headers={'Authorization': auth_header_str},
                                        verify=False)
                if response.status_code != status.HTTP_200_OK:
                    # iRODS user account does not exist and fails to be created, needs to delete the created
                    # linked account for next level of default user authentication
                    user.delete()
                    return None

            hashed_token = hashlib.sha256(access_token).hexdigest()[0:50]
            url = '{}registration/add_user_oids?username={}&subjectid={}&sessionid={}'.format(
                settings.DATA_REG_SERVICE_SERVER_URL,
                username, uid, hashed_token)
            response = requests.get(url, headers={'Authorization': auth_header_str}, verify=False)
            if response.status_code !=status.HTTP_200_OK:
                raise PermissionDenied(response.content)
            return user
        else:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
