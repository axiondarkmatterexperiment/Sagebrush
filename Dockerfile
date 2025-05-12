#FROM driplineorg/dripline-python:v5.0.0
FROM dripline-python:localCbi

COPY . /usr/local/src/dripline-python-plugin

WORKDIR /usr/local/src/dripline-python-plugin

RUN pip install pyModbusTCP
RUN pip install numpy
RUN pip install .
RUN apt-get update && apt-get install -y tini

WORKDIR /
#ENTRYPOINT ["/usr/local/src/dripline-python-plugin/sagebrush/entrypoint.sh"]
#CMD ["rsyslogd", "--no-daemon"]
