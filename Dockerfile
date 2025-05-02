FROM driplineorg/dripline-python:v5.0.0

COPY . /usr/local/src/dripline-python-plugin

WORKDIR /usr/local/src/dripline-python-plugin
RUN pip install .

WORKDIR /
