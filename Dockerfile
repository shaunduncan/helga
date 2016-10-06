FROM ubuntu:16.04

EXPOSE 6667 27017

RUN apt-get update -qq
RUN apt-get install -qqy --force-yes \
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

ADD setup.py /opt/helga
ADD helga/settings.py /opt/helga
WORKDIR /opt/helga

RUN ls -ltr /etc/

RUN sed -i -s 's/^bind_ip = 127.0.0.1/#bind_ip = 127.0.0.1/' /etc/mongodb.conf
RUN service mongodb restart

RUN pip install --upgrade pip

RUN cd /opt/helga && python setup.py install

ENV HELGA_SETTINGS=/opt/helga/settings.py

CMD helga
