ARG img_user=ghcr.io/driplineorg
ARG img_repo=dripline-python
ARG img_tag=v5.1.2

FROM ${img_user}/${img_repo}:${img_tag}

COPY . /usr/local/src/sagebrush

RUN apt-get update && apt-get install -y curl && \
    curl -O https://raw.githubusercontent.com/rabbitmq/rabbitmq-management/v3.7.8/bin/rabbitmqadmin && \
    chmod +x rabbitmqadmin && mv rabbitmqadmin /usr/local/bin/ && \
    echo $(uname -m)
    pip install --index-url=https://www.piwheels.org/simple scipy && \
    pip install pyModbusTCP && \
    cd /usr/local/src/sagebrush && \
    pip install .

#RUN apt-get update && apt-get install -y tini && apt-get install -y gdb

ENTRYPOINT ["/usr/local/src/sagebrush/sagebrush/entrypoint.sh"]
