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
                "score": doc['_score'],
                "filename": doc['_source']['filename'],
                "desc": doc['_source']['desc'],
                "res_type": 'Generic',
                "res_url": 'https://www.google.com',
                'res_title': doc['_id'],
                'res_creator': 'first creator',
                'res_create_time': 'May 17, 2018 at 2:11 p.m.',
                'res_update_time': 'May 17, 2018 at 2:11 p.m.'
            })

        return JsonResponse(response_data, status=status.HTTP_200_OK)
    else:
        response_data['message'] = "Please input a search term"
        response_data['results'] = []
        return JsonResponse(response_data, status=status.HTTP_400_BAD_REQUEST)
