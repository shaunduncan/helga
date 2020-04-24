FROM python:3

ADD . /code
WORKDIR /code
RUN pip install . tox
RUN tox
RUN pip list -o

ENTRYPOINT ["/usr/local/bin/helga"]
<<<<<<< HEAD

=======
>>>>>>> default to using docker settings for container
CMD ["--settings=settings-docker.py"]
