import json
import requests

from django.http import JsonResponse
from django.conf import settings
from rest_framework import status


def search_ds(coll):
    store = {}
    file = []
    folder = []
    if coll.data_objects:
        for files in coll.data_objects:
            file.append(files.name)
    if coll.subcollections:
        for folders in coll.subcollections:
            folder.append(folders.name)

    store['files'] = file
    store['folder'] = folder
    return store


# Create your views here.
def store(request):
    """
    Get file hierarchy for the requested endpoint directory in globus.
    It is invoked by an AJAX call, so it returns json object that holds content for files and folders
    under the requested directory/collection/subcollection
    """
    return_object = {}
    datastore = str(request.POST['store'])
    token = str(request.POST['token'])
    ds_uuid = str(request.POST['store_id'])
    # list file/dir entries for a given globus storage bucket id
    url = '{}registration/list_bucket?provider=globus&token={}&bucket_id={}'.format(settings.SERVICE_SERVER_URL,
                                                                                     token, ds_uuid)
    auth_header_str = 'Basic {}'.format(settings.DATA_REG_API_KEY)
    response = requests.get(url,
                            headers={'Authorization': auth_header_str},
                            verify=False)
    if response.status_code != status.HTTP_200_OK:
        # request fails
        return JsonResponse(status=response.status_code, data={'message': response.content})

    return JsonResponse(response.content)


def register(request):
    if request.method == 'POST':
        token = str(request.POST['token'])
        ds_uuid = str(request.POST['store_uuid'])
        path = str(request.POST['path'])
        # list file/dir entries for a given globus storage bucket id
        url = '{}registration/register_paths?provider=globus&token={}&bucket_id={}&paths={}'.format(
            settings.SERVICE_SERVER_URL, token, ds_uuid, path)
        auth_header_str = 'Basic {}'.format(settings.DATA_REG_API_KEY)
        response = requests.get(url,
                                headers={'Authorization': auth_header_str},
                                verify=False)
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
