# Set the base image to Python
FROM python:2.7.9
MAINTAINER code040@intelworks.com

# Environment
ENV DEBIAN_FRONTEND noninteractive

# Create the working dir and set the working directory
WORKDIR /

# Install dependencies
COPY ./requirements.txt /requirements.txt
RUN pip install -r requirements.txt \
    && pip install supervisor \
    && pip install gunicorn

# Install OpenTaxii
RUN mkdir /opentaxii
COPY ./ /opentaxii/
RUN cd  /opentaxii && python setup.py install && rm -rf /opentaxii

# Setup default config
COPY opentaxii/defaults.yml /opentaxi.yml
ENV OPENTAXII_CONFIG /opentaxii.yml

# Expose and Run
COPY docker-supervisord.conf /supervisord.conf
EXPOSE 9000
CMD ["supervisord","-c","/supervisord.conf"]

