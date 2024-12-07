ARG img_user=driplineorg
ARG img_repo=dripline-python
ARG img_tag=v4.7.1

FROM ${img_user}/${img_repo}:${img_tag}

COPY . /usr/local/src/sagebrush

WORKDIR /usr/local/src/sagebrush
RUN pip install .

WORKDIR /
