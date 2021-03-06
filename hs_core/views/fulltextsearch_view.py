import os
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import RequestError

from rest_framework import status
from rest_framework.exceptions import NotFound
from django.conf import settings
from django.http import JsonResponse

from hs_core.hydroshare.utils import get_resource_file_url
from hs_core.models import ResourceFile
from hs_core.views.utils import authorize, ACTION_TO_AUTHORIZE


if settings.FTS_URL:
    es = Elasticsearch([settings.FTS_URL])
else:
    es = None


def ftsearchview(request):
    term = request.GET.get('q', '')

    response_data = {}
    response_data["results"] = []
    if term:
        try:
            results = es.search(index="fts_index", doc_type="fts_doc",
                                q='contents:' + term,
                                _source_exclude=['contents'])
            hits = results['hits']['hits']
            res_id_list = []
            for doc in hits:
                rid = doc['_source']['guid']
                fname = doc['_source']['filename']
                id_to_search = rid + '-' + fname
                if id_to_search  in res_id_list:
                    continue
                try:
                    robj, authorized, _ = authorize(request, rid,
                                                    needed_permission=ACTION_TO_AUTHORIZE.VIEW_RESOURCE,
                                                    raises_exception=False)
                    if not authorized:
                        # only show resources the user has access to
                        continue
                except NotFound:
                    # only show resources hosted by the site
                    continue
                res_url = robj.get_absolute_url()
                res_type = robj.resource_type
                idx = res_type.find('Resource')
                if idx > 0:
                    res_type = res_type[:idx]
                res_title = robj.metadata.title.value
                res_creator = robj.first_creator.name
                res_create_time = robj.created.strftime('%m-%d-%Y at %I:%M %p')
                res_update_time = robj.updated.strftime('%m-%d-%Y at %I:%M %p')

                f_url = ''
                for f in ResourceFile.objects.filter(object_id=robj.id):
                    name_with_full_path = os.path.join(rid, 'data', fname)
                    if name_with_full_path == f.storage_path:
                        f_url = get_resource_file_url(f)
                        break

                response_data['results'].append({
                    "score": doc['_score'],
                    "filename": fname,
                    'file_url': f_url,
                    "res_type": res_type,
                    "res_url": res_url,
                    'res_title': res_title,
                    'res_creator': res_creator,
                    'res_create_time': res_create_time,
                    'res_update_time': res_update_time
                })
                res_id_list.append(id_to_search)

            return JsonResponse(response_data, status=status.HTTP_200_OK)

        except RequestError as ex:
            response_data['error'] = ex.info
            return JsonResponse(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return JsonResponse(response_data, status=status.HTTP_400_BAD_REQUEST)
