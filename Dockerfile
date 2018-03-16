FROM ubuntu:16.04

EXPOSE 6667 27017

RUN apt-get update -qq
RUN apt-get install -qqy \
	git \
	mongodb \
	ngircd \
	openssl \
	libssl-dev \
	python-dev \
	python-pip \
	python-setuptools \
	libffi6 \
	libffi-dev

ADD . /opt/helga
WORKDIR /opt/helga

RUN sed -i -s 's/^bind_ip = 127.0.0.1/#bind_ip = 127.0.0.1/' /etc/mongodb.conf && service mongodb restart

RUN pip install --upgrade pip
RUN pip install service_identity

RUN cd /opt/helga && python setup.py install


ENTRYPOINT ["/usr/local/bin/helga"]
