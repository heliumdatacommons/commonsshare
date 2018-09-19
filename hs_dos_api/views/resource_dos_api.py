import mimetypes
import logging
import os
import base64

from mezzanine.conf import settings

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import ValidationError, NotAuthenticated, PermissionDenied, NotFound

from hs_core import hydroshare
from hs_core.views import serializers
from hs_core.views.utils import authorize, ACTION_TO_AUTHORIZE

logger = logging.getLogger(__name__)


# Mixins
class ResourceToDataObjectListItemMixin(object):
    def resourceToDataObjectListItem(self, r):

        site_url = hydroshare.utils.current_site_url()
        istorage = r.get_irods_storage()
        irods_dest_prefix = "/" + settings.IRODS_ZONE + "/home/" + settings.IRODS_USERNAME

        urls = []
        for f in r.files.all():
            if f.reference_file_path:
                url = site_url + '/django_irods/download/' + f.resource.short_id + f.reference_file_path
                srcfile = f.reference_file_path
            else:
                url = site_url + '/django_irods/download/' + f.resource.short_id + '/data/' + f.short_path
                srcfile = os.path.join(irods_dest_prefix, f.storage_path)

            fsize = istorage.size(srcfile)
            checksum = istorage.get_checksum(srcfile)

            decoded_checksum = base64.b64decode(checksum).encode('hex')

            # trailing slash confuses mime guesser
            mimetype = mimetypes.guess_type(url)
            if mimetype[0]:
                ftype = mimetype[0]
            else:
                ftype = repr(None)

            urls.append({"url": url, "size": fsize, "mime_type": ftype, "checksum": decoded_checksum,
                         "checksum_type": 'sha256'})

        data_object_listitem = serializers.DataObjectListItem(dataobject_id=r.short_id,
                                                dataobject_name=r.metadata.title.value,
                                                date_created=r.created,
                                                date_last_updated=r.updated,
                                                urls = urls)
        return data_object_listitem


class DataObjectList(ResourceToDataObjectListItemMixin, generics.ListAPIView):
    """
    Get a list of data objects based on the following filter query parameters

    REST URL: dosapi/dataobjects/
    HTTP method: GET

        Supported query parameters (all are optional):

        :type   owner: str
        :type   from_date:  str (e.g., 2015-04-01)
        :type   to_date:    str (e.g., 2015-05-01)
        :param  owner: (optional) - to get a list of resources owned by a specified username
        :param  from_date: (optional) - to get a list of resources created on or after this date
        :param  to_date: (optional) - to get a list of resources created on or before this date
        :rtype:  json string
        :return:  a paginated list of resources with data for resource id, title, resource type,
        creator, public, date created, date last updated, resource bag url path, and science
        metadata url path

        example return JSON format for GET /dosapi/dataobjects/:

            {   "count":n
                "next": link to next page
                "previous": link to previous page
                "results":[
                        {"resource_id": resource id,
                        "date_last_updated": date resource last updated,
                        "public": true or false,
                        "resource_url": link to resource landing HTML page,
                ]
            }

    """
    pagination_class = PageNumberPagination

    def get(self, request):
        return self.list(request)

    # needed for list of resources
    def get_queryset(self):
        resource_list_request_validator = serializers.ResourceListRequestValidator(
            data=self.request.query_params)
        if not resource_list_request_validator.is_valid():
            raise ValidationError(detail=resource_list_request_validator.errors)

        filter_parms = resource_list_request_validator.validated_data
        filter_parms['user'] = (self.request.user if self.request.user.is_authenticated() else None)
        filter_parms['public'] = not self.request.user.is_authenticated()

        filtered_res_list = []

        for r in hydroshare.get_resource_list(**filter_parms):
            resource_list_item = self.resourceToDataObjectListItem(r)
            filtered_res_list.append(resource_list_item)

        return filtered_res_list

    def get_serializer_class(self):
        return serializers.DataObjectListItemSerializer


class DataObjectGet(ResourceToDataObjectListItemMixin, APIView):
    """
        Read a data object

        REST URL: dosapi/dataobject/{pk}
        HTTP method: GET
        :return: (on success): The dataobject in JSON format.

        :param  pk: dataobject id

        :raises:
        NotFound: return JSON format: {'detail': 'No data object was found for data object id':pk}
        PermissionDenied: return JSON format: {'detail': 'You do not have permission to perform
        this action.'}
        ValidationError: return JSON format: {parameter-1': ['error message-1'], 'parameter-2':
        ['error message-2'], .. }

        """
    pagination_class = PageNumberPagination

    def get(self, request, pk):
        """
        Get a dataobject in json format
        :param request:
        :param pk:
        :return:
        """
        res, _, _ = authorize(request, pk, needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE)
        ser = self.get_serializer_class()(self.resourceToDataObjectListItem(res))

        return Response(data=ser.data, status=status.HTTP_200_OK)

    def get_serializer_class(self):
        return serializers.DataObjectListItemSerializer