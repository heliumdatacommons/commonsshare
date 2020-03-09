# CommonsShare 

CommonsShare is Helium Team's Web User Interface that explores using the cloud to access and share FAIR Biomedical big data.

## Installation instructions to get CommonsShare web service up and running

In a production deployment of CommonsShare, [iRODS](http://irods.org) is used as the backend storage, and CommonsShare can be configured to interface with an iRODS server via iRODS python client and icommand iRODS interface once an iRODS server is up and running. CommonsShare is also dependent upon two services, namely, user authentication service and data registration service, to be completely functional. The instructions below cover the process and steps to install these two services on the same VM where the iRODS server has been installed. iRODS server installation is not covered here, but installation instructions for iRODS can be found [here](https://irods.org/download/).

### Installation instructions for user authentication service

Refer to [auth service installation instructions](https://github.com/heliumdatacommons/auth_microservice/blob/master/README.md) for detailed step-by-step installation guide. For CommonsShare user authentication to work in conjunction with iRODS, iRODS OAuth plugin also needs to be installed in iRODS server. Installation commands for iRODS OAuth plugin is also covered in this subsection. The source code and readme for iRODS OAuth plugin can be found [here](https://github.com/irods-contrib/irods_auth_plugin_openid/).

Supplemental notes:

- move `manage.py` from auth_microservice/auth_microservice directory to its parent directory auth_microservice. Otherwise, django command run will fail. In addition, make sure to run ```python manage.py migrate``` to migrate database tables after running setup script to create a database.
- put ssl key and certificates for commonsshare.org domain with right permission and configure them correctly in nginx.conf for user authentication service and in server_config.json for iRODS OAuth plugin.
- The example config.json.example file in the [github repo](https://github.com/heliumdatacommons/auth_microservice/blob/master/example/config/config.json.example) may not be sufficient for CommonsShare openid oauth user authentication to work in different scenarios. A config.json example in an existing working setup may need to be referred to in order to fill the gaps. An working example of config.json with domain-specific info stripped out is copied below for reference:


```
    {
        "allow_return_regex": ["^[\\w\\d\\-\\_]+\\.<my-domain>"],
        "redirect_uri": "https://<my-app>/authcallback",
        "root_return_to": "https://<my-app>/oauth_return",
        "root_default_provider": "auth0",
        "url_expiration_timeout": 3600,
        "real_time_validate_default": false,
        "real_time_validate_cache_retention_timeout": 60,
        "providers": {
            "globus": {
                "standard": "OpenID Connect",
                "client_id": "<client_id>",
                "client_secret": "<client_secret>",
                "metadata_url": "https://auth.globus.org/.well-known/openid-configuration",
                "introspection_endpoint": "https://auth.globus.org/v2/oauth2/token/introspect",
                "revocation_endpoint": "https://auth.globus.org/v2/oauth2/token/revoke"
            },
            "google": {
                "standard": "OpenID Connect",
                "client_id": "<client_id>",
                "client_secret": "<client_secret>",
                "metadata_url": "https://accounts.google.com/.well-known/openid-configuration",
                "introspection_endpoint": "https://www.googleapis.com/oauth2/v3/tokeninfo"
            },
            "auth0": {
                "standard": "OpenID Connect",
                "client_id": "<client_id>",
                "client_secret": "<client_secret>",
                "metadata_url": "https://heliumdatacommons.auth0.com/.well-known/openid-configuration",
                "userinfo_endpoint": "https://heliumdatacommons.auth0.com/userinfo",
                "login_endpoint": "https://heliumdatacommons.auth0.com/login"
            }
        }
    }
```

- If the VM has python 2.7 as the default python version, make sure you will use python3 to install the user authentication microservice. For example, run the command below to create an virtualenv using python3:
`python3 -m venv venv && source venv/bin/activate`. If python3 virtualenv is not installed, you can run the command below to install it: `sudo apt-get install python3-venv`. You can also run the following command sequences as needed to get system libraries and build environments ready for building the authentication microservices:

```
    sudo apt update && sudo apt dist-upgrade
    sudo apt install build-essential
    sudo apt install python3-dev
    sudo apt install python-dev
    sudo apt-get install python-psycopg2
    sudo apt-get install python3-psycopg2
    sudo apt-get update
    sudo apt-get install nginx
```

- After sudo su to auth_microservice user account, can add the following to .profile so that virtual environment is activated automatically when switching user to auth_microservice user account:

```
    export PATH
    cd ~/auth_microservice/
    source venv/bin/activate
```

- After sudo su to auth_microservice, need to run the following command in order to get virtual env set up correctly for the auth service:

```
    pip install --upgrade pip
    pip install wheel
    pip install psycopg2-binary
    pip install uwsgi
    pip install .
```

- Make sure to enable ssl connection by uncommenting 2 lines ```listen 443 default_server;``` and ```listen [::]:443 ssl default_server;``` while commenting the default listening to 80 lines in order to connect to the service via https ssl connection.
- Run the command ```echo Q > /tmp/auth_microservice.fifo``` to stop user auth microservice.
- Run the command ```echo r > /tmp/auth_microservice.fifo``` to start user auth microservice or just run ```uwsgi --ini ./uwsgi.ini``` to start user auth microservice if the echo command does not work.
- Run the command ```ps -ef | grep uwsgi``` to check whether user auth microservice process is running.
- Run the command ```tail -f -n 0 /tmp/auth_microservice.log``` to monitor auth service log when things are not working right.


#### Commands to get iRODS OAuth plugin installed and set up on iRODS server

**Install needed system packages**

```
   sudo apt install cmake
   sudo apt-get install irods-dev
   wget -qO - https://packages.irods.org/irods-signing-key.asc | sudo apt-key add -
   sudo apt-get install irods-externals-zeromq4-14.1.6-0
   sudo apt-get install libkrb5-dev
   sudo apt-get install libcurl4-gnutls-dev
```

**Install iRODS openid plugin**

```
   git clone https://github.com/irods-contrib/irods_auth_plugin_openid.git
   cd irods_auth_plugin_openid
   Update CMakeLists.txt to reflect the right iRODS version to build iRODS openid plugin again.
   export IRODS_EXTERNALS=/opt/irods-externals
   export PATH=$IRODS_EXTERNALS/cmake3.11.4-0/bin:$PATH
   mkdir build
   cd build
   cmake ..
   make
   sudo cp libopenid_client.so libopenid_server.so /usr/lib/irods/plugins/auth
```
If something goes wrong, build directory can be deleted and the cmake build process can start over

**Configure iRODS openid plugin**

Need to run ```curl -H "Authorization: Basic <admin_key>" "https://<user_auth_service_hostname>.commonsshare.org/admin/key?owner=irods"``` to get a API key for iRODS and put the API key into the following block in server_config.json in iRODS server:

```
"plugin_configuration": {
        "authentication": {
            "openid": {
                "default_provider": "auth0",
                "token_service": "https://<user_auth_service_hostname>.commonsshare.org",
                "token_service_key": "<API_KEY>",
                "token_exchange_min_port": 52000,
                "token_exchange_max_port": 52100
            }
        },
       ...
}
```


### Installation instructions for data registration service

Refer to [data registration service installation instructions](https://github.com/heliumdatacommons/data_registration_service/blob/master/README.md) for detailed step-by-step installation guide.

Supplemental notes:

- After sudo su to data_registration_service, need to run the following commands in order to get virtual env set up correctly for the service:

```
    pip install --upgrade pip
    pip install wheel
    pip install psycopg2-binary
    pip install uwsgi
    pip install .
```

- Need to call the command ```curl -H "Authorization: Basic 7e93116d2910ee54b9afacca26f31f49e41bd7932cfbab8eb2642b7e7861e904" "https://scidas-icat.commonsshare.org/registration/admin/create_key?owner=CommonsShare"``` to create an API key to set in CommonsShare local_settings.py as data registration API key.

- Make sure to change ALLOWED_HOSTS in src/microservice/microservice/settings.py

### Other miscellaneous supplemental notes

- Can run ```iadmin modresc demoResc name commonssharehelxResc``` to rename demoResc to whatever resource for the project, then update server_config.json, core.re, and irods_environment.json to replace demoResc with the renamed resource as the default resource for iRODS server, rules, and icommands.
- Update core.re to replace msiCreateCollByAdmin rule with the following to work around an iRODS bug that inherit attribute is not honored when creating a new user by rods admin:

```
    acCreateCollByAdmin(*parColl,*childColl) {
      msiCollCreate(*parColl ++ "/" ++ *childColl, 0, *status);
      msiSetACL("default", "own", $otherUserName, *parColl ++ "/" ++ *childColl);
      msiSetACL("default", "null", $userNameClient, *parColl ++ "/" ++ *childColl);
    }
```

- Commands to run to create needed iRODS user and resource for interfacing with CommonsShare

```
    iadmin mkuser bagsdata#commonssharescidasZone rodsuser
    iadmin moduser bagsdata#commonssharescidasZone password <pwd>
    imkdir /commonssharescidasZone/data
    imkdir /commonssharescidasZone/data/bagsdata
    ichmod own bagsdata /commonssharescidasZone/data/bagsdata
    ichmod -rM read bagsdata /commonssharescidasZone/home
    ichmod -rM inherit /commonssharescidasZone/home
    ichmod -rM inherit /commonssharescidasZone/data

```

### Installation instructions for CommonsShare

- Install docker

```
    curl -fsSL https://get.docker.com/ | sh
    sudo usermod -aG docker <user>
    sudo systemctl start docker
    sudo systemctl status docker
    sudo systemctl enable docker
```
    Run `docker version` from that user to verify docker works. You may need to log out, then log back in to get rid of the permission defined error.

- Install docker-compose

```
    sudo curl -L https://github.com/docker/compose/releases/download/1.24.0/docker-compose-`uname -s`-`uname -m` -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
```
    Run `docker-compose --version` to verify docker-compose works.

- Create commons-service account and use it as the service account to install CommonsShare. Make sure to add commons-service into docker group so that this service account can run docker.


## Historical instructions

For reference, the following are historical instructions mostly inherited from 
[HydroShare](http://github.com/hydroshare/hydroshare) since CommonsShare was cloned from HydroShare initially.

#### Nightly Build Status generated by [Jenkins CI](http://ci.hydroshare.org:8080) (develop branch)

| Workflow | Clean | Build/Deploy | Unit Tests | Flake8 | Requirements |
| -------- | ----- | ------------ | ---------- | -------| ------------ |
| [![Build Status](http://ci.hydroshare.org:8080/job/nightly-build-workflow/badge/icon?style=plastic)](http://ci.hydroshare.org:8080/job/nightly-build-workflow/) | [![Build Status](http://ci.hydroshare.org:8080/job/nightly-build-clean/badge/icon?style=plastic)](http://ci.hydroshare.org:8080/job/nightly-build-clean/) | [![Build Status](http://ci.hydroshare.org:8080/job/nightly-build-deploy/badge/icon?style=plastic)](http://ci.hydroshare.org:8080/job/nightly-build-deploy/) | [![Build Status](http://ci.hydroshare.org:8080/job/nightly-build-test/badge/icon?style=plastic)](http://ci.hydroshare.org:8080/job/nightly-build-test/) | [![Build Status](http://ci.hydroshare.org:8080/job/nightly-build-flake8/badge/icon?style=plastic)](http://ci.hydroshare.org:8080/job/nightly-build-flake8/) | [![Requirements Status](https://requires.io/github/hydroshare/hs_docker_base/requirements.svg?branch=develop)](https://requires.io/github/hydroshare/hs_docker_base/requirements/?branch=master) | 

CommonsShare is a website and hydrologic information system for sharing hydrologic data and models aimed at providing the cyberinfrastructure needed to enable innovation and collaboration in research to solve water problems. CommonsShare is designed to advance hydrologic science by enabling the scientific community to more easily and freely share products resulting from their research, not just the scientific publication summarizing a study, but also the data and models used to create the scientific publication. With CommonsShare users can: (1) share data and models with colleagues; (2) manage who has access to shared content; (3) share, access, visualize and manipulate a broad set of hydrologic data types and models; (4) use the web services API to program automated and client access; (5) publish data and models to meet the requirements of research project data management plans; (6) discover and access data and models published by others; and (7) use web apps to visualize, analyze, and run models on data in CommonsShare.

More information can be found in our [Wiki Pages](https://github.com/hydroshare/hydroshare/wiki)

## Install

This README file is for developers interested in working on the CommonsShare code itself, or for developers or researchers learning about how the application works at a deeper level. If you simply want to _use_ the application, go to http://hydroshare.org and register an account.

If you want to install and run the source code of application locally and/or contribute to development, read on.

### [VirtualBox](https://www.virtualbox.org/wiki/Downloads) development environment

To quickly get started developing we offer a preconfigured development environment encapsulated within a virtual box Virtual Machine (VM). This includes the appropriate version of Ubuntu, Python, Docker, and other key dependencies and development tools.

### Simplified Installation Instructions 
1. Download the [latest OVA file here](http://distribution.hydroshare.org/public_html/)
2. Open the .OVA file with VirtualBox, this will create a guest VM
3. Follow the instructions here to share a local hydroshare folder with your guest VM
4. Start the guest VM
5. Log into the guest VM with either ssh or the GUI. The default username/password is hydro:hydro
6. From the root directory `/home/hydro`, clone this repository into the hydroshare folder
7. `cd` into the hydroshare folder and run `./hsctl rebuild --db` to build the application and run it
8. If all goes well, your local version of CommonsShare should be running at http://192.168.56.101:8000

For more detailed installation, please see this document: [Getting Started with CommonsShare](https://github.com/hydroshare/hydroshare/wiki/getting_started)

### Local MacOS Installation
1. Install brew and get the latest version of bash on your mac by running "brew install bash"
2. Install docker for MacOS.  It now includes Docker Compose in the installation so no need to download that separately.
3. Get the commonsshare code into a local directory by cloning or branching the current repository.
4. In the config subdirectory of your commonshare code installation, change the hydroshare-config.yaml file to point to your local file paths.
4. Run the hsctl script with the rebuild --db option.
5. Access the image at localhost:8000 with userid of "admin" and password of "default".

## Usage

For all intents and purposes, CommonsShare is a large Python/Django application with some extra features and technologies added on:
- SOLR for searching
- Redis for caching
- RabbitMQ for concurrency and serialization
- iRODS for a federated file system
- PostgreSQL for the database backend

#### The `hsctl` Script

The `hsctl` script is your primary tool in interacting with and running tasks against your CommonsShare install. It has the syntax `./hsccl [command]` where `[command]` is one of:

- `loaddb`: Deletes existing database and reloads the database specified in the `hydroshare-config.yaml` file.
- `managepy [args]`: Executes a `python manage.py [args]` call on the running hydroshare container.
- `maint_off`: Removes the maintenance page from view (only if NGINX is being used).
- `maint_on`: Displays the maintenance page in the browser (only if NGINX is being used).
- `rebuild`: Stops, removes and deletes only the hydroshare docker containers and images while retaining the database contents on the subsequent build as defined in the `hydroshare-config.yaml` file
- `rebuild --db`: Fully stops, removes and deletes any prior hydroshare docker containers, images and database contents prior to installing a clean copy of the hydroshare codebase as defined in the `hydroshare-config.yaml` file.
- `rebuild_index`: Rebuilds the solr/haystack index in a non-interactive way.
- `restart`: Restarts the django server only (and nginx if applicable).
- `start`: Starts all containers as defined in the `docker-compose.yml` file (and nginx if applicable).
- `stop`: Stops all containers as defined in the `docker-compose.yml` file.
- `update_index`: Updates the solr/haystack index in a non-interactive way.

## Testing and Debugging

### Testing

Tests are run via normal Django tools and conventions. However, you should use the `hsctl` script mentioned abouve with the `managepy` command. For example: `./hsctl managepy test hs_core.tests.api.rest.test_resmap --keepdb`.

There are currently over 600 tests in the system, so it is highly recommended that you run the test suites separately from one another.

### Debugging

You can debug via PyCharm by following the instructions [here](https://github.com/hydroshare/hydroshare/wiki/pycharm-configuration).

## Other Configuration Options

### Local iRODS

Local iRODS is _not_ required for development unless you are specifically working on the iRODS integration. However,if you want to work with iRODS or you simply want to learn about it, you can enable it locally.

### Local HTTPS

To enable HTTPS locally:
1. edit `config/hydroshare-config.template` and change the two values under `### Deployment Options ###` to `true` like so:
```
### Deployment Options ###
USE_NGINX: true
USE_SSL: true
```
2. Run `./hsctl rebuild`

## Contribute

There are many ways to contribute to CommonsShare. Review [Contributing guidelines](https://github.com/hydroshare/hydroshare/blob/develop/docs/contributing.rst) and github practices for information on
1. Opening issues for any bugs you find or suggestions you may have
2. Developing code to contribute to CommonsShare 
3. Developing a CommonsShare App
4. Submiting pull requests with code changes for review

## License 

CommonsShare is released under the BSD 3-Clause License. This means that [you can do what you want, so long as you don't mess with the trademark, and as long as you keep the license with the source code](https://tldrlegal.com/license/bsd-3-clause-license-(revised)).

©2017 CUAHSI. This material is based upon work supported by the National Science Foundation (NSF) under awards 1148453 and 1148090. Any opinions, findings, conclusions, or recommendations expressed in this material are those of the authors and do not necessarily reflect the views of the NSF.
