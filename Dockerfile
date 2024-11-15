from driplineorg/dripline-python:v4.5.8

COPY . /usr/local/src/dripline-python-plugin

WORKDIR /usr/local/src/dripline-python-plugin
RUN pip install .

WORKDIR /
