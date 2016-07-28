FROM python:3.4.5
MAINTAINER EclecticIQ <opentaxii@eclecticiq.com>

# Create the working dir and set the working directory
WORKDIR /

# Install dependencies
COPY ./requirements.txt /requirements.txt
RUN pip install -r requirements.txt \
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

# Expose and Run in gunicorn
EXPOSE 9000
CMD ["gunicorn", "opentaxii.http:app", "--bind 0.0.0.0:9000"]
