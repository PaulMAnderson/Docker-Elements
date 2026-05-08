# Want to a minimal ubuntu install with :
# Ubuntu 22.04 - Because comes with python 3.10
# Python 3.10.x
# CudNN 8.6
# Cuda 11.8
# tensorflow-2.12.0
# Pytorch 2.4.0
# Phy
# Also want an open gl capable rendering system and a vnc server so I can do phy sorting
# And I want Positron server (an older one!)

FROM ghcr.io/selkies-project/nvidia-glx-desktop:22.04

# Set a bunch of environmental variables
ENV SHELL=/bin/bash  
ENV USER=root
ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY_SIZEW=1920 
ENV DISPLAY_SIZEH=1080 
ENV DISPLAY_REFRESH=60 
ENV DISPLAY_DPI=96
ENV DISPLAY_CDEPTH=24
ENV UID=99
ENV GID=100
ENV USERNAME=ubuntu
ENV UMASK=002

# Change the user id and group to Unraid standards
USER root
RUN usermod -u $UID -g $GID $USERNAME
# Adjust ownership of the user's home directory and any files owned by the old UID/GID
RUN find / -path /proc -prune -o -path /sys -prune -o -path /dev -prune -o -user 1000 -exec chown -h $UID {} \; && \
    find / -path /proc -prune -o -path /sys -prune -o -path /dev -prune -o -group 1000 -exec chgrp -h $GID {} \;

# Install open ssh and setup ssh access
RUN apt-get update && apt-get install -y \
    curl \
    rsync \
    netcat-traditional \
    mg \
    vim \
    bzip2 \
    zip \
    unzip \
    git \
    wget \
    apt-utils \
    build-essential \
    openssh-server

# Switch back to the updated user
USER $USERNAME

# Add umask 002 to the .bashrc
RUN echo 'umask 002' >> ~/.bashrc

# RUN apt-get update && apt-get install -y --no-install-recommends \
#     python3.10 \
#     python3-pip \
#     python3-dev \
#     python-is-python3 \
#     ffmpeg \
#     libsm6 \
#     libxext6 \
#     libnss3 \
#     libxcb-icccm4 \
#     libxcb-image0 \
#     libxcb-keysyms1 \
#     libxcb-render-util0-dev \
#     libxcb-xinerama0
#     # qtwebengine5-dev \
#     # libqt5quickcontrols2-5 \
#     # libqt5multimedia5 \
#     # libqt5webengine5 \
#     # libqt5quick5 \
#     # libqt5qml5 \
#     # libqt5pdf5

# RUN apt-get autoclean -y && \
#     apt-get autoremove -y && \
#     apt-get clean && \
#     rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN python3 -m pip install --upgrade pip

# use pip to install tensorflow
# pip install tensorflow[and-cuda]=2.12

# Install my versions of Open-Ephys, SpikeInterface and Neo
RUN pip install git+https://github.com/PaulMAnderson/open-ephys.git

# Install my versions of Open-Ephys, SpikeInterface and Neo
RUN pip install git+https://github.com/PaulMAnderson/python-neo.git
RUN pip install git+https://github.com/PaulMAnderson/spikeinterface.git
# RUN pip install --upgrade 'setuptools>61.0.0'
# RUN pip install git+https://github.com/PaulMAnderson/open-ephys.git
RUN pip install docker

# use pip to install pytorch
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# use pip to install deeplabcut
RUN pip install \
    ipython \
    jupyter \
    'notebook<7.0.0' \
    'tables==3.8.0' \
    "git+https://github.com/DeepLabCut/DeepLabCut.git@pytorch_dlc#egg=deeplabcut[gui,modelzoo,wandb,tf]"

# Now kilosort
RUN pip install kilosort

# Install phy
RUN pip install git+https://github.com/cortex-lab/phy.git

RUN pip install -U pyqt5

# Expose the default VS Code Server port
EXPOSE 8080

# And SSH? Not sure this is needed
EXPOSE 22

# Config Jupyter Server
RUN jupyter server --generate-config
RUN echo "c.ServerApp.password = 'sha1:41eb0095b22f:18586ae781ed9292674508cdb380469f26a8a1d4'" >> ${HOME}/.jupyter/jupyter_server_config.py
EXPOSE 8888

# Make an empty data processing directory so it is avaliable later
RUN mkdir /mnt/data\ processing

# Add command to start jupyter lab to supervisord
RUN echo "\n" >> /etc/supervisord.conf && \
    echo "[program:jupyterlab]" >> /etc/supervisord.conf && \
    echo "command=jupyter lab --ip=0.0.0.0 --ServerApp.root_dir=/mnt/data\ processing --no-browser --allow-root --port=8888" >> /etc/supervisord.conf && \
    echo "autostart=true" >> /etc/supervisord.conf && \
    echo "autorestart=true" >> /etc/supervisord.conf && \
    echo "user=root >> /etc/supervisord.conf" && \
    echo "stderr_logfile=/tmp/jupyterlab.err.log" >> /etc/supervisord.conf && \
    echo "stdout_logfile=/tmp/jupyterlab.out.log"   >> /etc/supervisord.conf

# Add command to start ssh to supervisord
RUN echo "\n" >> /etc/supervisord.conf && \
    echo "[program:sshd]" >> /etc/supervisord.conf && \
    echo "command=/usr/sbin/sshd -D" >> /etc/supervisord.conf && \
    echo "autostart=true" >> /etc/supervisord.conf && \
    echo "autorestart=true" >> /etc/supervisord.conf && \
    echo "startretries=5" >> /etc/supervisord.conf && \
    echo "stderr_logfile=/tmp/ssh.err.log" >> /etc/supervisord.conf && \
    echo "stderr_logfile_maxbytes=10MB" >> /etc/supervisord.conf && \
    echo "stdout_logfile=/tmp/ssh.out.log" >> /etc/supervisord.conf && \
    echo "stdout_logfile_maxbytes=10MB" >> /etc/supervisord.conf

USER root
# Add SSH configuration
RUN mkdir -p /var/run/sshd /root/.ssh /etc/ssh && \
    echo "PasswordAuthentication no" >> /etc/ssh/sshd_config && \
    echo "PubkeyAuthentication yes" >> /etc/ssh/sshd_config && \
    echo "PermitRootLogin no" >> /etc/ssh/sshd_config && \
    echo "ChallengeResponseAuthentication no" >> /etc/ssh/sshd_config && \
    echo "AuthorizedKeysFile .ssh/authorized_keys" >> /etc/ssh/sshd_config && \
    ssh-keygen -A

# Add test user for debugging ssh
# RUN useradd -m -d /home/testuser -s /bin/bash testuser
# RUN echo "testuser:password" | chpasswd
# RUN mkdir -p /home/testuser/.ssh
# RUN chmod 700 /home/testuser/.ssh
# RUN chown -R testuser:testuser /home/testuser/.ssh


# Add keys
COPY authorized_keys /root/.ssh/authorized_keys
RUN mkdir -p /home/ubuntu/.ssh
COPY authorized_keys /home/ubuntu/.ssh/authorized_keys
RUN chown -R ubuntu:users /home/ubuntu/.ssh
RUN chown -R ubuntu:users /etc/ssh/ssh_host*
RUN chmod 600 /home/ubuntu/.ssh/authorized_keys /root/.ssh/authorized_keys && \
    chmod 700 /home/ubuntu/.ssh /root/.ssh && \
    chmod 755 /etc/ssh

USER $USERNAME

# CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--allow-root", "--no-browser"]

# echo "numprocs=1" >> /etc/supervisord.conf && \
    # echo "startsecs=0" >> /etc/supervisord.conf && \
    # echo "process_name=%(program_name)s_%(process_num)02d" >> /etc/supervisord.conf && \
