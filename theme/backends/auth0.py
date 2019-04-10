"""
Auth0 Auth backend that authenticates user created using info returned from oauth service, docs at:
    https://github.com/heliumdatacommons/auth_microservice/wiki/API-and-Use
"""

import requests
import hashlib

from json import loads
from rest_framework import status

from django.contrib.auth.models import User, Group
from django.core.exceptions import PermissionDenied
from django.conf import settings

from hs_core.hydroshare.users import create_account


class Auth0OAuth2:
    def authenticate(self, request, username=None, access_token=None, first_name=None,
                     last_name=None, email='', uid=None):

        if not access_token or not username:
            return None

        url = '{}validate_token'.format(settings.OAUTH_SERVICE_SERVER_URL)
        auth_header_str = 'Basic {}'.format(settings.OAUTH_APP_KEY)
        response = requests.get(url, headers={'Authorization': auth_header_str},
                                params={'provider': 'auth0',
                                        'access_token': access_token})
        if response.status_code != status.HTTP_200_OK:
            return None
        else:
            return_data = loads(response.content)
            active = return_data['active']
            if not active:
                return None
            else:
                preferred_username = return_data['username']

        # set email field to username if not returned from auth service
        if not email:
            email = username

        if username == preferred_username:
            auth_header_str = 'Basic {}'.format(settings.DATA_REG_API_KEY)
            try:
                user = User.objects.get(username=username)
                # update user email field if needed
                if user.email != email:
                    user.email = email
                    user.save()

            except User.DoesNotExist:
                user = create_account(email=email, username=username, first_name=first_name,
                                      last_name=last_name, superuser=False, active=True)
                if settings.DATA_REG_SERVICE_SERVER_URL:
                    # create corresponding iRODS account with same username via OAuth if not exist
                    # already
                    url = '{}registration/create_account?username={}&zone={}&auth_name={}'.format(
                        settings.DATA_REG_SERVICE_SERVER_URL, username, settings.IRODS_ZONE, uid)
                    response = requests.get(url,
                                            headers={'Authorization': auth_header_str},
                                            verify=False)
                    if response.status_code != status.HTTP_200_OK:
                        # iRODS user account does not exist and fails to be created, needs to delete
                        # the created linked account for next level of default user authentication
                        user.delete()
                        return None

            if settings.DATA_REG_SERVICE_SERVER_URL:
                hashed_token = hashlib.sha256(access_token).hexdigest()[0:50]
                url = '{}registration/add_user_oids?username={}&subjectid={}&sessionid={}'.format(
                    settings.DATA_REG_SERVICE_SERVER_URL,
                    username, uid, hashed_token)
                response = requests.get(url, headers={'Authorization': auth_header_str}, verify=False)
                if response.status_code !=status.HTTP_200_OK:
                    raise PermissionDenied(response.content)

            if settings.WHITE_LIST_LOGIN:
                # needs to make sure the user is in a whitelist group before logging them in
                in_whitelist = False
                excl_group = Group.objects.get(name='CommonsShare Author')
                if excl_group:
                    groups = Group.objects.all().exclude(pk=excl_group.pk)
                else:
                    groups = Group.objects.all()
                for g in groups:
                    if user in g.gaccess.members:
                        in_whitelist = True
                        break
                if in_whitelist:
                    return user
                else:
                    raise PermissionDenied("You are not in the white list to be authorized to log "
                                           "in CommonsShare")
            else:
                return user
        else:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
