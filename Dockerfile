ARG img_user=driplineorg
ARG img_repo=dripline-python
ARG img_tag=v_admxApp_1

FROM ${img_user}/${img_repo}:${img_tag}

WORKDIR /usr/local/src/dripline-python-plugin

RUN pip install pyModbusTCP
RUN pip install numpy
COPY . /usr/local/src/sagebrush

WORKDIR /usr/local/src/sagebrush
RUN pip install .
#RUN apt-get update && apt-get install -y tini && apt-get install -y gdb

WORKDIR /
ENTRYPOINT ["/usr/local/src/dripline-python-plugin/sagebrush/entrypoint.sh"]
