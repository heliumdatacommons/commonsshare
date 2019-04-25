import json
import os
import string
import requests

from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required

from rest_framework import status

from irods.session import iRODSSession
from irods.manager.collection_manager import CollectionManager

from django_irods.icommands import SessionException
from hs_core import hydroshare
from hs_core.views.utils import authorize, ACTION_TO_AUTHORIZE, get_size_and_avu_for_irods_ref_files
from hs_core.hydroshare import utils


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

def check_upload_files(resource_cls, fnames_list):
    file_types = resource_cls.get_supported_upload_file_types()
    valid = False
    ext = ''
    if file_types == ".*":
        valid = True
    else:
        for fname in fnames_list:
            ext = os.path.splitext(fname)[1].lower()
            if ext == file_types:
                valid = True
            else:
                for index in range(len(file_types)):
                    file_type_str = file_types[index].strip().lower()
                    if file_type_str == ".*" or ext == file_type_str:
                        valid = True
                        break

    return (valid, ext)


@login_required
def get_openid_token(request):
    uid = request.session.get('subject_id', '')
    response_data = {}
    if not uid:
        response_data['error'] = "cannot retrieve user's subject id to request token"
        return JsonResponse(response_data, status=status.HTTP_400_BAD_REQUEST)
    url = 'token?uid={}&provider=auth0&scope=openid%20email%20profile'.format(uid)
    # note that trailing slash should not be added to return_to url
    # return_url = '&return_to={}://{}/irods/openid_return'.format(request.scheme, request.get_host())
    # req_url = '{}{}{}'.format(settings.OAUTH_SERVICE_SERVER_URL, url, return_url)
    req_url = '{}{}'.format(settings.OAUTH_SERVICE_SERVER_URL, url)
    auth_header_str = 'Basic {}'.format(settings.OAUTH_APP_KEY)
    response = requests.get(req_url,
                            headers={'Authorization': auth_header_str},
                            verify=False)
    if response.status_code == status.HTTP_401_UNAUTHORIZED:
        # the user is not authorized
        return_data = json.loads(response.text)
        response_data['authorization_url'] = return_data['authorization_url']
        return JsonResponse(response_data, status=status.HTTP_401_UNAUTHORIZED)
    elif response.status_code == status.HTTP_200_OK:
        # the user is already authorized, directly use the returned token
        return_data = json.loads(response.content)
        if 'access_token' in return_data:
            response_data['token'] = return_data['access_token']
            return JsonResponse(response_data, status=status.HTTP_200_OK)
        else:
            response_data['error'] = 'no access_token is returned from token request:' + response.content
            return JsonResponse(response_data, status=status.HTTP_400_BAD_REQUEST)
    else:
        response_data['error'] = response.text
        return JsonResponse(response_data, status=status.HTTP_400_BAD_REQUEST)


# Create your views here.
def store(request):
    """
    Get file hierarchy (collection of subcollections and data objects) for the requested directory
    in an iRODS zone the requested user has logged in.
    It is invoked by an AJAX call, so it returns json object that holds content for files and folders
    under the requested directory/collection/subcollection
    """
    return_object = {}
    irods_sess = iRODSSession(user=request.user.username, access_token=str(request.POST['token']),
                              zone=settings.IRODS_ZONE, host=settings.IRODS_HOST,
                              authentication_scheme='openid', openid_provider='auth0',
                              port=settings.IRODS_PORT)
    datastore = str(request.POST['store']).strip()
    if datastore.endswith('/'):
        datastore = datastore[:-1]

    try:
        coll_manager = CollectionManager(irods_sess)
        coll = coll_manager.get(datastore)
    except Exception as ex:
        res = JsonResponse({'error': ex.message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return res

    store = search_ds(coll)

    return_object['files'] = store['files']
    return_object['folder'] = store['folder']
    jsondump = json.dumps(return_object)
    irods_sess.cleanup()
    return HttpResponse(
        jsondump,
        content_type = "application/json"
    )

def upload(request):
    if request.method == 'POST':
        file_names = str(request.POST['upload'])
        fnames_list = string.split(file_names, ',')

        resource_cls = hydroshare.check_resource_type(request.POST['res_type'])
        valid, ext = check_upload_files(resource_cls, fnames_list)

        response_data = {}
        if valid:
            response_data['file_type_error'] = ''
            response_data['irods_file_names'] = file_names
            # get selected file names without path for informational display on the page
            response_data['irods_sel_file'] = ', '.join(os.path.basename(f.rstrip(os.sep)) for f in fnames_list)
        else:
            response_data['file_type_error'] = "Invalid file type: {ext}".format(ext=ext)
            response_data['irods_file_names'] = ''
            response_data['irods_sel_file'] = 'No file selected.'

        return HttpResponse(
            json.dumps(response_data),
            content_type = "application/json"
        )
    else:
        return HttpResponse(
            json.dumps({"error": "Not POST request"}),
            content_type="application/json"
        )

def upload_add(request):
    # add irods file into an existing resource
    res_id = request.POST['res_id']
    resource, _, _ = authorize(request, res_id, needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE)
    res_files = request.FILES.getlist('files')
    extract_metadata = request.POST.get('extract-metadata', 'No')
    extract_metadata = True if extract_metadata.lower() == 'yes' else False
    irods_fnames = request.POST.get('irods_file_names', '')
    irods_fnames_list = string.split(irods_fnames, ',')
    res_cls = resource.__class__

    # TODO: read resource type from resource, not from input file
    valid, ext = check_upload_files(res_cls, irods_fnames_list)
    source_names = []

    if not valid:
        request.session['file_type_error'] = "Invalid file type: {ext}".format(ext=ext)
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    else:
        # TODO: this should happen whether resource is federated or not
        irods_fsizes = []
        irods_avus = {}
        if irods_fnames:
            source_names = irods_fnames.split(',')
            try:
                irods_fsizes, irods_avus = get_size_and_avu_for_irods_ref_files(irods_fnames=irods_fnames)
            except SessionException as ex:
                request.session['validation_error'] = ex.stderr
                return HttpResponseRedirect(request.META['HTTP_REFERER'])

    try:
        utils.resource_file_add_pre_process(resource=resource, files=res_files, user=request.user,
                                            extract_metadata=extract_metadata, 
                                            source_names=source_names, folder=None)
    except hydroshare.utils.ResourceFileSizeException as ex:
        request.session['file_size_error'] = ex.message
        return HttpResponseRedirect(request.META['HTTP_REFERER'])

    except (hydroshare.utils.ResourceFileValidationException, Exception) as ex:
        request.session['validation_error'] = ex.message
        return HttpResponseRedirect(request.META['HTTP_REFERER'])

    try:
        hydroshare.utils.resource_file_add_process(resource=resource, files=res_files, 
                                                   user=request.user,
                                                   extract_metadata=extract_metadata,
                                                   is_file_reference=True,
                                                   source_names=source_names,
                                                   source_sizes=irods_fsizes, folder=None)

    except (hydroshare.utils.ResourceFileValidationException, Exception) as ex:
        if ex.message:
            request.session['validation_error'] = ex.message
        elif ex.stderr:
            request.session['validation_error'] = ex.stderr
    except SessionException as ex:
        request.session['validation_error'] = ex.stderr

    # add extra metadata if irods_avus is not empty
    if irods_avus:
        updated_metadata = resource.extra_metadata
        if updated_metadata:
            updated_metadata.update(irods_avus)
        else:
            updated_metadata = irods_avus
        resource.extra_metadata = updated_metadata
        resource.save()

    request.session['resource-mode'] = 'edit'
    return HttpResponseRedirect(request.META['HTTP_REFERER'])

