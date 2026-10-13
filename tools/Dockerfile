FROM ubuntu:24.04
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential autoconf flex bison help2man ca-certificates curl git \
    python3 python3-dev python3-venv python3-pip python3-numpy python3-pil \
    yosys ngspice kicad kicad-symbols kicad-footprints kicad-packages3d \
    xvfb xauth fonts-dejavu-core && rm -rf /var/lib/apt/lists/*
RUN apt-get update && apt-get install -y --no-install-recommends libfl-dev && rm -rf /var/lib/apt/lists/*
ARG VERILATOR_VERSION=5.040
RUN curl -fL https://github.com/verilator/verilator/archive/refs/tags/v${VERILATOR_VERSION}.tar.gz -o /tmp/verilator.tar.gz \
    && sha256sum /tmp/verilator.tar.gz > /opt/verilator-source.sha256 \
    && tar xzf /tmp/verilator.tar.gz -C /tmp \
    && cd /tmp/verilator-${VERILATOR_VERSION} && autoconf \
    && ./configure --prefix=/opt/verilator && make -j4 && make install \
    && rm -rf /tmp/verilator*
RUN python3 -m venv --system-site-packages /opt/venv
COPY requirements.txt /tmp/requirements.txt
RUN /opt/venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt
ENV PATH="/opt/venv/bin:/opt/verilator/bin:${PATH}"
ENV MPLBACKEND=Agg
WORKDIR /work
