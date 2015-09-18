# Set the base image to Python
FROM python:2.7.9
MAINTAINER Intelworks <opentaxii@intelworks.com>

# Create the working dir and set the working directory
WORKDIR /

# Install dependencies
COPY ./requirements.txt /requirements.txt
RUN pip install -r requirements.txt \
    && pip install supervisor \
    && pip install gunicorn \
    && pip install psycopg2 \
    && rm -f /requirements.txt


# Create directories
RUN mkdir /opentaxii \
    && mkdir /data \
    && mkdir /input

# Setup OpenTAXII
COPY ./ /opentaxii/
RUN cd  /opentaxii \
    && python setup.py install \
    && rm -rf /opentaxii

# Setup default config
COPY opentaxii/defaults.yml /opentaxii.yml

# Volume for exposing data and possible input
VOLUME [ "/data", "/input" ]

# Setup the entrypoint
COPY docker/entrypoint.sh /entrypoint.sh
ENTRYPOINT [ "/entrypoint.sh" ]

# Expose and Run using supervisor
COPY docker/supervisord.conf /supervisord.conf
EXPOSE 9000
CMD ["supervisord","-c","/supervisord.conf"]

