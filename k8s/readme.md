# Get CommonsShare to run on Kubernetes cluster

These yaml files for Kubernetes deployment in this directory were initially created from [Kompose](http://kompose.io/) followed by further customization based on workflows outlined in <https://www.digitalocean.com/community/tutorials/how-to-migrate-a-docker-compose-workflow-to-kubernetes>

To deploy CommonsShare to Kubernetes, run the following command:
```
kubectl create -f postgis-claim0-persistentvolumeclaim.yaml,postgis-deployment.yaml,rabbitmq-deployment.yaml,solr-deployment.yaml,hydroshare-service.yaml,hydroshare-deployment.yaml,hydroshare-env-configmap.yaml,defaultworker-env-configmap.yaml,defaultworker-deployment.yaml,postgis-service.yaml
```

The problems we currently run into is how to create initial database with migrations after containers are up. Without handling this properly, defaultworker pod cannot run due to the following error:
```
  File "/hydroshare/hs_core/hydroshare/utils.py", line 368, in current_site_url
    current_site = Site.objects.get_current()
  File "/usr/local/lib/python2.7/site-packages/django/contrib/sites/models.py", line 63, in get_current
    return self._get_site_by_id(site_id)
  File "/usr/local/lib/python2.7/site-packages/django/contrib/sites/models.py", line 35, in _get_site_by_id
    site = self.get(pk=site_id)
  File "/usr/local/lib/python2.7/site-packages/django/db/models/manager.py", line 85, in manager_method
    return getattr(self.get_queryset(), name)(*args, **kwargs)
  File "/usr/local/lib/python2.7/site-packages/django/db/models/query.py", line 374, in get
    num = len(clone)
  File "/usr/local/lib/python2.7/site-packages/django/db/models/query.py", line 232, in __len__
    self._fetch_all()
  File "/usr/local/lib/python2.7/site-packages/django/db/models/query.py", line 1121, in _fetch_all
    self._result_cache = list(self._iterable_class(self))
  File "/usr/local/lib/python2.7/site-packages/django/db/models/query.py", line 53, in __iter__
    results = compiler.execute_sql(chunked_fetch=self.chunked_fetch)
  File "/usr/local/lib/python2.7/site-packages/django/db/models/sql/compiler.py", line 899, in execute_sql
    raise original_exception
django.db.utils.ProgrammingError: relation "django_site" does not exist
LINE 1: ..."django_site"."domain", "django_site"."name" FROM "django_si...

```