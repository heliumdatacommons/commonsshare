from elasticsearch import Elasticsearch

from django.conf import settings

from mezzanine.pages.page_processors import processor_for


es = Elasticsearch([settings.FTS_URL])


@processor_for('fulltextsearch')
def fulltextsearch(request, page):
    term = request.args.get('q')

    results = []
    msg = ''

    if term:
        results = es.search(index="test_index", doc_type="post",
                            body={"query": {"match": {"content": term}}})
        msg = "%d documents found matching the term <b><i><u>%s</u></i></b>" % \
              (results['hits']['total'], term)

        for doc in results['hits']['hits']:
            'results'.append({
                "id": doc['_id'],
                "filename": doc['_source']['filename'],
                "desc": doc['_source']['desc']
            })

    context = {'message': msg,
               'results': results}
    return context
