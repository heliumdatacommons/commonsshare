"""
OAuth2 token based authentication for REST API
"""

import requests

from json import loads

from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework import authentication

from django.contrib.auth.models import User
from django.conf import settings

class OAuth2Authentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        http_auth = request.META.get('HTTP_AUTHORIZATION')
        if http_auth:
            auth_header = request.META.get('HTTP_AUTHORIZATION').strip()
            auth_strs = auth_header.split(' ')
            if auth_strs[0] == 'Bearer':
                token = auth_strs[1]

                url = '{}validate_token'.format(settings.OAUTH_SERVICE_SERVER_URL)
                auth_header_str = 'Basic {}'.format(settings.OAUTH_APP_KEY)
                response = requests.get(url, headers={'Authorization': auth_header_str},
                                        params={'provider': 'auth0',
                                                'access_token': token})
                if response.status_code != status.HTTP_200_OK:
                    raise AuthenticationFailed('Token is not valid')
                else:
                    return_data = loads(response.content)
                    active = return_data['active']
                    if not active:
                        raise AuthenticationFailed("Token is expired")
                    else:
                        username = return_data['username']

                try:
                    user = User.objects.get(username=username)
                except User.DoesNotExist:
                    raise AuthenticationFailed('User does not exist')

                return (user, None)
        else:
            return (None, None)
