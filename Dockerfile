FROM python:3.6-stretch AS build
LABEL maintainer="EclecticIQ <opentaxii@eclecticiq.com>"

RUN python3 -m venv /venv && /venv/bin/pip install -U pip setuptools

COPY ./requirements.txt ./requirements-docker.txt /opentaxii/
RUN /venv/bin/pip install -r /opentaxii/requirements.txt -r /opentaxii/requirements-docker.txt

COPY . /opentaxii
RUN /venv/bin/pip install /opentaxii


FROM python:3.6-slim-stretch AS prod
LABEL maintainer="EclecticIQ <opentaxii@eclecticiq.com>"
COPY --from=build /venv /venv

RUN mkdir /data /input
VOLUME ["/data", "/input"]

COPY ./docker/entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

EXPOSE 9000
ENV PATH "/venv/bin:${PATH}"
ENV PYTHONDONTWRITEBYTECODE "1"
CMD ["/venv/bin/gunicorn", "opentaxii.http:app", "--workers=2", \
     "--log-level=info", "--log-file=-", "--timeout=300", \
     "--config=python:opentaxii.http", "--bind=0.0.0.0:9000"]
