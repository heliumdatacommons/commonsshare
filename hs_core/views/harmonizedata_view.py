import requests
from json import loads

from rest_framework import status

from django.http import JsonResponse
from django.utils.http import urlquote


def hdsearchview(request):
    term = request.GET.get('q', '')
    response_data = {}
    response_data["results"] = []
    if term:
        url = 'https://scigraph-ontology.monarchinitiative.org/scigraph/vocabulary/search/{}/'.\
            format(urlquote(term))
        response = requests.get(url)
        if response.status_code != status.HTTP_200_OK:
            return JsonResponse({'message': response.text}, status=response.status_code)

        return_data = loads(response.content)
        response_data = {}
        response_data["results"] = []
        for item in return_data:
            response_data['results'].append({
                'iri': item['iri'],
                'labels': ', '.join(item['labels']) if item['labels'] else '',
                'curie': item['curie'],
                'categories': ', '.join(item['categories']) if item['categories'] else '',
                'synonyms': ', '.join(item['synonyms']) if item['synonyms'] else '',
                'definitions': ', '.join(item['definitions']) if item['definitions'] else ''
            })

        return JsonResponse(response_data, status=status.HTTP_200_OK)
    else:
        return JsonResponse(response_data, status=status.HTTP_400_BAD_REQUEST)
