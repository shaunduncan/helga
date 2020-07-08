FROM python:2

ADD . /helga
WORKDIR /helga

RUN pip install . tox
RUN tox
RUN pip list -o

ENTRYPOINT ["/usr/local/bin/helga"]
CMD ["--settings=settings-docker.py"]
