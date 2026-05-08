ARG ROOT_IMAGE=paultklab/python:base

FROM $ROOT_IMAGE

# Change to user for ownership of install packages
USER ${UID}
WORKDIR /tmp

# CEBRA install instructions from - https://cebra.ai/docs/installation.html
# First pytables
RUN conda install -c conda-forge 'pytables==3.8.0'

# Then pytorch with gpu support
COPY requirements-cuda.txt .
RUN pip install -r requirements-cuda.txt

# Then pip for conda
RUN pip install 'cebra[dev,demos,docs,integrations,datasets]'

# Prepare Cebra folder
RUN mkdir "/home/${USER}/cebra"
WORKDIR "/home/${USER}/cebra"

# Download notebooks
RUN git clone https://github.com/AdaptiveMotorControlLab/CEBRA-demos demo_notebooks

# Download data 
# RUN wget --content-disposition 'https://figshare.com/ndownloader/files/36869049?private_link=60adb075234c2cc51fa3' && \
#     mkdir data && \
#     tar -xvf "data.tgz" -C "data" && \
#     rm data.tgz

WORKDIR $HOME

# Change user details
ENV USER="cebra"
ENV UID="99"
ENV GID="100"
ENV GROUP="users"
ENV PASSWORD="cebra"
ENV HOME="/home/${USER}"

#Give access to the GPU
ENV CUDA_VISIBLE_DEVICES=all

# Try and make sure Conda is available
ENV PATH="/opt/conda/bin:${PATH}"
ENV CUDA_VISIBLE_DEVICES=0

USER root
