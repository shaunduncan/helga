FROM python:3

ADD . /code
WORKDIR /code

RUN pip install .

RUN pip install tox

RUN tox

RUN pip list -o

ENTRYPOINT ["/usr/local/bin/helga"]
