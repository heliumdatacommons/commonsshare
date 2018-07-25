from elasticsearch import Elasticsearch

from rest_framework import status
from django.conf import settings
from django.http import JsonResponse


es = Elasticsearch([settings.FTS_URL])


def ftsearchview(request):
    term = request.GET.get('q', '')

    response_data = {}
    if term:
        results = es.search(index="test_index", doc_type="post",
                            body={"query": {"match": {"content": term}}})
        response_data['message'] = "%d documents found matching the term <b><i><u>%s</u></i></b>" \
                                   % (results['hits']['total'], term)
        response_data["results"] = []
        for doc in results['hits']['hits']:
            response_data['results'].append({
                "id": doc['_id'],
                "filename": doc['_source']['filename'],
                "desc": doc['_source']['desc']
            })

        return JsonResponse(response_data, status=status.HTTP_200_OK)
    else:
        response_data['message'] = "Please input a search term"
        return JsonResponse(response_data, status=status.HTTP_400_BAD_REQUEST)
