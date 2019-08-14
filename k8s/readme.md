# Get CommonsShare to run on Kubernetes cluster

These yaml files for Kubernetes deployment in this directory were initially created from [Kompose](http://kompose.io/) followed by further customization based on workflows outlined in <https://www.digitalocean.com/community/tutorials/how-to-migrate-a-docker-compose-workflow-to-kubernetes>. To simplify kubernetes deployment of CommonsShare, we added an option to allow CommonsShare not to use iRODS as data storage backend. We also combined solr and hydroshare containers into the same pod due to volume sharing needs between the containers.

To deploy CommonsShare to Kubernetes, run the following command:
```
kubectl create -f postgis-claim0-persistentvolumeclaim.yaml,postgis-deployment.yaml,hydroshare-service.yaml,hydroshare-solr-deployment.yaml,hydroshare-env-configmap.yaml,postgis-service.yaml
```

# Problems and Solutions

* The following have been done to get rid of kompose convert warnings:

  * Add ```version: '3'``` on the top of docker-compose.yaml file to get rid of ```unsupported env_file key - ignoring``` warning.  
  * Add ```services:``` line after the ```version: '3'``` line to get rid of ```FATA defaultworker Additional property defaultworker is not allowed``` error.

* The following has been added to hydroshare-deployment.yaml to resolve database connection error:
```
initContainers:
      - name: init-postgis
        image: busybox
        command: ['sh', '-c', 'until nc -z postgis:5432; do echo waiting for postgis; sleep 2; done;']
```

* Simplified CommonsShare down to 3 containers, hydroshare, solr, and postgis with defaultworker and rabbitmq containers removed since celery tasks have not been used in CommonsShare at this point.

* Extracted commands from hsctl control script into container initialization bash scripts to be run when containers are initialized in kubernetes pods, e.g., init-hydroshare, init-postgis, init-solr, to address database migration, static file collection, solr index update, etc. Since solr needs to access /hydroshare volume from hydroshare container, combined two containers into one pod deployment, i.e., hydroshare-solr-deployment.yaml, for easy volume sharing. This results in two pods for CommonsShare to be deployed by Kubernetes.

* minikube does not directly support loadBalancer <https://github.com/kubernetes/minikube/issues/4113>. Ended up running```minikube tunnel``` in order to emulate loadBalancer to get external ip; otherwise, will have pending external ip forever.
