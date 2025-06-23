
ARG img_user=ghcr.io/driplineorg
ARG img_repo=dripline-python
ARG img_tag=v_admx_1


FROM ${img_user}/${img_repo}:${img_tag}
RUN apt-get update && apt-get install -y curl
RUN curl -O https://raw.githubusercontent.com/rabbitmq/rabbitmq-management/v3.7.8/bin/rabbitmqadmin && \
   chmod +x rabbitmqadmin && mv rabbitmqadmin /usr/local/bin/
WORKDIR /usr/local/src/dripline-python-plugin

RUN pip install pyModbusTCP
RUN pip install numpy
COPY . /usr/local/src/sagebrush

WORKDIR /usr/local/src/sagebrush
RUN pip install .


#RUN apt-get update && apt-get install -y tini && apt-get install -y gdb

WORKDIR /
ENTRYPOINT ["/usr/local/src/sagebrush/sagebrush/entrypoint.sh"]
