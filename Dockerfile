#FROM driplineorg/dripline-python:v5.0.0
FROM dripline-python:localCbi

COPY . /usr/local/src/dripline-python-plugin

WORKDIR /usr/local/src/dripline-python-plugin

RUN pip install pyModbusTCP
RUN pip install .

WORKDIR /
