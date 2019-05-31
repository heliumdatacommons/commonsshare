from uuid import uuid4
import os
import mimetypes

from rest_framework.decorators import api_view

from django_irods import icommands
from django_irods.storage import IrodsStorage
from django.conf import settings
from django.http import HttpResponse, FileResponse
from django.core.exceptions import PermissionDenied

from hs_core.views.utils import authorize, ACTION_TO_AUTHORIZE
from hs_core.hydroshare.resource import FILE_SIZE_LIMIT
from hs_core.signals import pre_download_file
from hs_core.hydroshare import check_resource_type
from hs_core.hydroshare.hs_bagit import create_bag

from . import models as m
from .icommands import Session, GLOBAL_SESSION


def download(request, path, rest_call=False, use_async=True, *args, **kwargs):

    split_path_strs = path.split('/')
    is_bag_download = False
    if split_path_strs[0] == 'bags':
        res_id = os.path.splitext(split_path_strs[1])[0]
        is_bag_download = True
    else:
        res_id = split_path_strs[0]
    res, authorized, _ = authorize(request, res_id,
                                   needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE,
                                   raises_exception=False)
    if not authorized:
        response = HttpResponse(status=401)
        content_msg = "You do not have permission to download this resource!"
        if rest_call:
            raise PermissionDenied(content_msg)
        else:
            signin_html = '</h1><div class="col-xs-12"><h2 class="page-title">' \
                          '<a href="/oauth_request/"><span class ="glyphicon glyphicon-log-in"></span>' \
                          'Sign In</a></h2>'
            response.content = '<h1>' + content_msg + signin_html
            return response

    if not is_bag_download and "/data" not in path:
        idx_sep = path.find('/')
        path = path[idx_sep:]

    istorage = IrodsStorage()

    if 'environment' in kwargs:
        environment = int(kwargs['environment'])
        environment = m.RodsEnvironment.objects.get(pk=environment)
        session = Session("/tmp/django_irods", settings.IRODS_ICOMMANDS_PATH,
                          session_id=uuid4())
        session.create_environment(environment)
        session.run('iinit', None, environment.auth)
    elif getattr(settings, 'IRODS_GLOBAL_SESSION', False):
        session = GLOBAL_SESSION
    elif icommands.ACTIVE_SESSION:
        session = icommands.ACTIVE_SESSION
    else:
        raise KeyError('settings must have IRODS_GLOBAL_SESSION set '
                       'if there is no environment object')

    if istorage.exists(res_id) and is_bag_download:
        bag_modified = istorage.getAVU(res_id, 'bag_modified')
        # make sure if bag_modified is not set to true, we still recreate the bag if the
        # bag file does not exist for some reason to resolve the error to download a nonexistent
        # bag when bag_modified is false due to the flag being out-of-sync with the real bag status

        if bag_modified is None or bag_modified.lower() == "false":
            # check whether the bag file exists
            bag_file_name = res_id + '.zip'
            bag_full_path = os.path.join('bags', bag_file_name)

            if not istorage.exists(bag_full_path):
                bag_modified = 'true'

        if bag_modified is None or bag_modified.lower() == "true":
            create_bag(res)

    resource_cls = check_resource_type(res.resource_type)

    # send signal for pre download file
    download_file_name = split_path_strs[-1]
    pre_download_file.send(sender=resource_cls, resource=res,
                           download_file_name=download_file_name,
                           request=request)

    # obtain mime_type to set content_type
    mtype = 'application-x/octet-stream'
    mime_type = mimetypes.guess_type(path)
    if mime_type[0] is not None:
        mtype = mime_type[0]
    # retrieve file size to set up Content-Length header
    stdout = session.run("ils", None, "-l", path)[0].split()
    flen = int(stdout[3])
    options = ('-',)  # we're redirecting to stdout.
    proc = session.run_safe('iget', None, path, *options)
    response = FileResponse(proc.stdout, content_type=mtype)
    response['Content-Disposition'] = 'attachment; filename="{name}"'.format(
        name=path.split('/')[-1])
    response['Content-Length'] = flen
    return response


@api_view(['GET'])
def rest_download(request, path, *args, **kwargs):
    """
    download a resource bag or file
    :param request:
    :param path:
    :param args:
    :param kwargs:
    :return:
    """
    # need to have a separate view function just for REST API call
    return download(request, path, rest_call=True, *args, **kwargs)
