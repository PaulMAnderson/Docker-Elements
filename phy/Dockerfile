ARG ROOT_IMAGE=paultklab/python:base

FROM $ROOT_IMAGE

# Change user details
ENV USER="phy"
ENV UID="99"
ENV GID="100"
ENV GROUP="users"
ENV PASSWORD="phy"
ENV HOME="/home/${USER}"

USER root

# Install X11 and Qt dependencies for X11 forwarding
RUN apt-get update && apt-get install -y \
    libxcb-xinerama0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-xfixes0 \
    libxkbcommon-x11-0 \
    libxcb-shape0 \
    libxcb-xkb1 \
    libgl1 \
    libglib2.0-0 \
    libdbus-1-3 \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p "/home/${USER}/.cache" && \
    chown -R ${UID}:${GID} "/home/${USER}"

USER ${UID}

WORKDIR /tmp

# Install phy requirements via mamba
RUN mamba install --yes \
    'cython' \
    'dask' \
    'h5py' \
    'joblib' \
    'matplotlib-base' \
    'numpy' \
    'pillow' \
    'pyopengl' \
    'pyqt' \
    'pyqtwebengine' \
    'pytest' \
    'qtconsole' \
    'requests' \
    'responses' \
    'scikit-learn' \
    'scipy' \
    'traitlets' \
    && mamba clean --all -f -y

# Install phy and your custom packages
RUN pip install --no-cache-dir \
    git+https://github.com/cortex-lab/phy.git

WORKDIR $HOME

USER root