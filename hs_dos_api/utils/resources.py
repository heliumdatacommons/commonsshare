from hs_core.views import serializers
from rest_framework.exceptions import ValidationError, NotAuthenticated, PermissionDenied, NotFound

def get_resource_list(request):
    resource_list_request_validator = serializers.ResourceListRequestValidator(data=request.query_params)
    
    if not resource_list_request_validator.is_valid():
        raise ValidationError(detail=resource_list_request_validator.errors)
        filter_parms = resource_list_request_validator.validated_data
        filter_parms['user'] = (request.user if request.user.is_authenticated() else None)
        if len(filter_parms['type']) == 0:
            filter_parms['type'] = None
        else:
            filter_parms['type'] = list(filter_parms['type'])

        filter_parms['public'] = not request.user.is_authenticated()

        filtered_res_list = []

        for r in hydroshare.get_resource_list(**filter_parms):
            resource_list_item = resourceToResourceListItem(r)
            filtered_res_list.append(resource_list_item)

        return filtered_res_list