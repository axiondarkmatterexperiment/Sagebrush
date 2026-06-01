ARG img_user=ghcr.io/driplineorg
ARG img_repo=dripline-python
ARG img_tag=v5.1.5

FROM ${img_user}/${img_repo}:${img_tag}

SHELL ["/bin/bash", "-c"]

COPY . /usr/local/src/sagebrush

RUN apt-get update && apt-get install -y curl && \
    curl -O https://raw.githubusercontent.com/rabbitmq/rabbitmq-management/v3.7.8/bin/rabbitmqadmin && \
    chmod +x rabbitmqadmin && mv rabbitmqadmin /usr/local/bin/ && \
    arch=$(uname -m) && \
    echo "Architecture: ${arch}" && \
    pip_installs="pyModbusTCP numpy" && \
    if [[ $arch != arm ]] && [[ $arch != "armv7"* ]]; then \
        pip_installs="${pip_installs} scipy"; \
    fi && \
    pip3 install ${pip_installs} && \
    cd /usr/local/src/sagebrush && \
    pip install .

#RUN apt-get update && apt-get install -y tini && apt-get install -y gdb

ENTRYPOINT ["/usr/local/src/sagebrush/sagebrush/entrypoint.sh"]
