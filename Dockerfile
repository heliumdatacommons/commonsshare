FROM hydroshare/hs_docker_base:release-1.9.7
MAINTAINER Phuong Doan pdoan@cuahsi.org

USER root

RUN pip install --upgrade pip

# inplaceedit in pip doesn't seem compatible with Django 1.11 yet...
RUN pip uninstall -y django-inplaceedit
RUN pip install git+https://github.com/theromis/django-inplaceedit.git@e6fa12355defedf769a5f06edc8fc079a6e982ec

RUN pip uninstall -y python-irodsclient
RUN pip install git+https://github.com/theferrit32/python-irodsclient.git@openid

RUN pip install \
    minid \
    haystack_queryparser \
    elasticsearch

WORKDIR /hydroshare

CMD ["/bin/bash"]
