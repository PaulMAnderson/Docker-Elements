ARG ROOT_IMAGE=paultklab/python:base

FROM $ROOT_IMAGE

# Some extras we may need
RUN apt-get update && apt-get install -y \
    zlib1g \
    ffmpeg \
    gfortran \
    && rm -rf /var/lib/apt/lists/*

# Need to downgrade python
RUN rm /opt/conda/conda-meta/pinned && \
    conda init bash && \
    conda install 'python<=3.11' -n base

# Clone lightning-pose 
RUN git clone https://github.com/paninski-lab/lightning-pose.git lightning-pose
WORKDIR lightning-pose

# Install lightning-pose
RUN pip install -e ".[dev,extra_models]" && \
    pip install fiftyone-db-ubuntu2204

# Configure environment
ENV USER="lightning"
ENV UID="99"
ENV GID="100"
ENV GROUP="users"
ENV PASSWORD="lightning"

ENV HOME="/home/${USER}"
# nvidia-container-runtime
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=all
ENV CUDA_VISIBLE_DEVICES=0

WORKDIR ${HOME}

# Switch to root to launch supervisor
USER root
