from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from hs_dos_api import utils
import json
 
@api_view(['GET'])
def get_databundle_list(request):
    """ get databundle list """
    # databundle_list = utils.get_databundle_list(request)
    sample_response = """
    {
        "data_bundles": [
            {
            "id": "string",
            "data_object_ids": [
                "string"
            ],
            "created": "2018-05-17T19:47:57.891Z",
            "updated": "2018-05-17T19:47:57.891Z",
            "version": "string",
            "checksums": [
                {
                "checksum": "string",
                "type": "string"
                }
            ],
            "description": "string",
            "aliases": [
                "string"
            ],
            "system_metadata": {
                "additionalProp1": {}
            },
            "user_metadata": {
                "additionalProp1": {}
            }
            }
        ],
        "next_page_token": "string"
    }
    """

    return Response(json.loads(sample_response))

@api_view(['GET'])
def get_databundle_versions(request):
    """ get databundle versions """
    return Response({
        "method": request.method
    })

@api_view(['POST'])
def create_databundle(request):
    """ create a new databundle. """
    # write same logic
    return Response({
        "method": request.method
    })

@api_view(['GET', 'PUT', 'DELETE'])
def get_update_delete_databundle(request, pk):
    "get, update or delete a databundle by ID."
    # write same logic
    return Response({
        "method": request.method,
        "pk": pk
    })
