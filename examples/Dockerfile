FROM intelworks/opentaxii:latest
MAINTAINER code040@intelworks.com

RUN pip install mysql-python

COPY services.yml /services.yml
COPY collections.yml /collections.yml
COPY docker-entrypoint.sh /entrypoint.sh

ENV OPENTAXII_AUTH_SECRET "SOME SECRET"
ENV OPENTAXII_DOMAIN "localhost:9000"
ENV OPENTAXII_USER ""
ENV OPENTAXII_PASS ""
ENV DB_USER  ""
ENV DB_PASS  ""
ENV DB_NAME  ""
ENV DB_HOST  ""
ENV DB_PORT  ""

ENTRYPOINT ["./entrypoint.sh"]
CMD [ "supervisord","-c","/supervisord.conf" ]
