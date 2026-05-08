ARG ROOT_IMAGE=paultklab/python:base

FROM $ROOT_IMAGE

# Copy requirements.txt
USER root
COPY requirements.txt /tmp/requirements.txt
RUN chown -R ${UID}:${GID} /tmp/requirements.txt

# Some extras we may need
RUN apt-get update && apt-get install -y \
    zlib1g \
    ffmpeg \
    gfortran \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /tmp
USER ${UID}

# Install DeepLabCut 
RUN mamba install -y \
    'pytables==3.8.0' \
    'pip' \
    'ipython' \
    'jupyter' \
    'nb_conda' \
    'notebook<7.0.0' \
    'ffmpeg'

RUN pip install -r requirements.txt
RUN pip install "deeplabcut[gui,modelzoo,wandb]=='3.0.0rc10'"

# Configure environment
ENV HOME="/home/${USER}"
# nvidia-container-runtime
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=all
ENV CUDA_VISIBLE_DEVICES=0

# Switch to root to launch supervisor
USER root
