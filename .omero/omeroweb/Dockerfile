ARG OMEROWEB_BASE_IMAGE=openmicroscopy/omero-web:latest
FROM $OMEROWEB_BASE_IMAGE

USER root
RUN yum install -y -q \
    java-11-openjdk \
    git && \
    rm -rf /var/cache/yum
USER omero-web
