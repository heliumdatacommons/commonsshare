import json
import requests

from django.http import JsonResponse
from django.conf import settings
from rest_framework import status


# Create your views here.
def store(request):
    """
    Get file hierarchy for the requested endpoint directory or for the requested bucket path from globus if path is
    not empty in the request.
    It is invoked by an AJAX call, so it returns json object that holds content for files and folders
    under the requested endpoint
    """
    return_object = {}
    token = str(request.POST['token'])
    ds_uuid = str(request.POST['store_id'])
    path = str(request.POST['path'])
    if path:
        # list file/dir entries for a given globus storage bucket id
        url = '{}registration/list_bucket_path?provider=globus&token={}&bucket_id={}&path={}'.format(
            settings.SERVICE_SERVER_URL, token, ds_uuid, path)
    else:
        # list file/dir entries for a given globus storage bucket id
        url = '{}registration/list_bucket?provider=globus&token={}&bucket_id={}'.format(settings.SERVICE_SERVER_URL,
                                                                                        token, ds_uuid)
    auth_header_str = 'Basic {}'.format(settings.DATA_REG_API_KEY)
    response = requests.get(url,
                            headers={'Authorization': auth_header_str},
                            verify=False)
    if response.status_code != status.HTTP_200_OK:
        # request fails
        return JsonResponse(status=response.status_code, data={'error': response.content})

    return_data = json.loads(response.content)

    return_object = {}
    file = []
    folder = []
    for lst in return_data['listings']:
        if lst['type'] == 'dir':
            folder.append(lst['name'])
        elif lst['type'] == 'file':
            file.append(lst['name'])

    return_object['files'] = file
    return_object['folder'] = folder
    return JsonResponse(return_object)


def register(request):
    if request.method == 'POST':
        uid = str(request.POST['uid'])
        ds_uuid = str(request.POST['store_uuid'])
        path = str(request.POST['path'])

        # create iRODS resource first before registering the path
        url = '{}registration/create_resource?rescname={}&subjectid={}'.format(
            settings.SERVICE_SERVER_URL, ds_uuid, uid)
        auth_header_str = 'Basic {}'.format(settings.DATA_REG_API_KEY)

        response = requests.get(url, headers={'Authorization': auth_header_str}, verify=False)

        if response.status_code != status.HTTP_200_OK:
            # request fails
            return JsonResponse(status=response.status_code, data={'error': response.content})

        p_data = {
            'provider': 'globus',
            'bucket_id': ds_uuid,
            'paths': [path]
        }

        # list file/dir entries for a given globus storage bucket id
        url = '{}registration/register_paths'.format(settings.SERVICE_SERVER_URL)
        response = requests.post(url, data=json.dumps(p_data), headers={'Authorization': auth_header_str}, verify=False)
        if response.status_code != status.HTTP_200_OK:
            # request fails
            return JsonResponse(status=response.status_code, data={'error': response.content})

        return JsonResponse(
            response.content
        )
    else:
        return JsonResponse(
            status= 400,
            data = json.dumps({"error": "Not POST request"})
        )
