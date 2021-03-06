# Get CommonsShare to run on Kubernetes cluster

These yaml files for Kubernetes deployment in this directory were initially created from [Kompose](http://kompose.io/) followed by further customization based on workflows outlined in <https://www.digitalocean.com/community/tutorials/how-to-migrate-a-docker-compose-workflow-to-kubernetes>. To simplify kubernetes deployment of CommonsShare, we added an option to allow CommonsShare not to use iRODS as data storage backend. We also combined solr and hydroshare containers into the same pod due to volume sharing needs between the containers.

To deploy CommonsShare to Kubernetes, run the following command:
```
kubectl create -f postgis-claim0-persistentvolumeclaim.yaml,postgis-deployment.yaml,hydroshare-service.yaml,solr-deployment.yaml,hydroshare-env-configmap.yaml,hydroshare-secret.yaml,postgis-service.yaml,solr-service.yaml,hydroshare-deployment.yaml
```

# Problems and Solutions

* The following have been done to get rid of kompose convert warnings:

  * Add ```version: '3'``` on the top of docker-compose.yaml file to get rid of ```unsupported env_file key - ignoring``` warning.  
  * Add ```services:``` line after the ```version: '3'``` line to get rid of ```FATA defaultworker Additional property defaultworker is not allowed``` error.

* Simplified CommonsShare down to 3 containers, hydroshare, solr, and postgis with defaultworker and rabbitmq containers removed since celery tasks have not been used in CommonsShare at this point.

* To avoid volume sharing between solr and commonsshare pods, created a custom solr image that includes schema.xml file in the image along with creating the schema collection for commonsshare on solr server and starting the solr server. 

* Extracted commands from hsctl control script into container initialization bash scripts to be run when containers are initialized in kubernetes pods, e.g., init-hydroshare, init-postgis, init-solr, to address database migration, static file collection, solr index update, etc.

* The following has been added to hydroshare-deployment.yaml to resolve database connection error and solr connection error:
```
initContainers:
      - name: init-postgis
        image: busybox
        command: ['sh', '-c', 'until nc -z postgis:5432; do echo waiting for postgis; sleep 2; done;']
      - name: init-solr
        image: busybox
        command: ['sh', '-c', 'until nc -z solr:8983; do echo waiting for solr; sleep 2; done;']  
```

* minikube does not directly support loadBalancer <https://github.com/kubernetes/minikube/issues/4113>. Ended up running```minikube tunnel``` in order to emulate loadBalancer to get external ip; otherwise, will have pending external ip forever.

* To build a cs-k8s image, follow the steps below:

  * run commands below to have the right files ready for k8s deployment in the image:
  ```
  cp gunicorn_start-k8s gunicorn_start
  cp Dockerfile-k8s Dockerfile
  cp init-hydroshare-k8s init-hydroshare
  cp init-postgis-k8s init-postgis
  cp init-solr-k8s init-solr
  cp pg.development-k8s.sql pg.development.sql
  ```
  
  * build the image by running ```docker build -t cs-k8s .``` in commonsshare directory.
  
