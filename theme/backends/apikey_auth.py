"""
APIKey user authentication for REST API
"""

import requests

from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework import authentication

from django.contrib.auth.models import User
from django.conf import settings


class APIKeyAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION').strip()
        auth_strs = auth_header.split(' ')
        if auth_strs[0] == 'APIKey':
            auth_info_strs = auth_strs[1].split(':')
            username = auth_info_strs[0].strip()
            key = auth_info_strs[1].strip()

            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                raise AuthenticationFailed('User does not exist')

            url = '{}apikey/verify'.format(settings.OAUTH_SERVICE_SERVER_URL)
            auth_header_str = 'Basic {}'.format(settings.OAUTH_APP_KEY)
            response = requests.get(url, headers={'Authorization': auth_header_str},
                                    params={'username': username,
                                            'key': key})
            if response.status_code != status.HTTP_200_OK:
                raise AuthenticationFailed('API key is not valid')

            return (user, None)
