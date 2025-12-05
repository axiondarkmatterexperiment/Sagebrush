ARG img_user=ghcr.io/driplineorg
ARG img_repo=dripline-python
ARG img_tag=v5.1.2

FROM ${img_user}/${img_repo}:${img_tag}

SHELL ["/bin/bash", "-c"]

COPY . /usr/local/src/sagebrush

RUN apt-get update && apt-get install -y curl wget && \
    curl -O https://raw.githubusercontent.com/rabbitmq/rabbitmq-management/v3.7.8/bin/rabbitmqadmin && \
    chmod +x rabbitmqadmin && mv rabbitmqadmin /usr/local/bin/ && \
    arch=$(uname -m) && \
    echo "architecture: ${arch}" && \
    pip_installs="pyModbusTCP numpy" && \
    if [[ $arch != arm ]] && [[ $arch != "armv7"* ]]; then \
        pip_installs="${pip_installs} scipy" && \
        echo "No, this is not arm or armv7"; \
        #wget https://www.piwheels.org/simple/scipy/scipy-1.16.3-cp311-cp311-linux_armv7l.whl#sha256=d9466489287e758403b3245da07149677abeb32f3e5f63b0b095cb7805b4b857 && \
        #pip3 install scipy-1.16.3-cp311-cp311-linux_armv7l.whl; \
    fi && \
    pip3 install ${pip_installs} && \
    cd /usr/local/src/sagebrush && \
    pip install .

#RUN apt-get update && apt-get install -y tini && apt-get install -y gdb

ENTRYPOINT ["/usr/local/src/sagebrush/sagebrush/entrypoint.sh"]
