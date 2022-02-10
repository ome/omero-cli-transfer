ARG OMEROSERVER_BASE_IMAGE=openmicroscopy/omero-server:latest
FROM $OMEROSERVER_BASE_IMAGE

USER root
RUN yum install -y -q \
    git && \
    rm -rf /var/cache/yum
USER omero-server
