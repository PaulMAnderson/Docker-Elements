# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

# Ubuntu 24.04 (noble)
# https://hub.docker.com/_/ubuntu/tags?page=1&name=noble
ARG ROOT_IMAGE=ubuntu:24.04

FROM $ROOT_IMAGE

ARG USER="python"
ARG UID="99"
ARG GID="100"
ARG GROUP="users"
ARG PASSWORD="python"

# Fix: https://github.com/hadolint/hadolint/wiki/DL4006
# Fix: https://github.com/koalaman/shellcheck/wiki/SC3014
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

USER root

# Install all OS dependencies for the Server that starts
# but lacks all features (e.g., download as all possible file formats)
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update --yes && \
    # - `apt-get upgrade` is run to patch known vulnerabilities in system packages
    #   as the Ubuntu base image is rebuilt too seldom sometimes (less than once a month)
    apt-get upgrade --yes && \
    apt-get install --yes --no-install-recommends \
    # - bzip2 is necessary to extract the micromamba executable.
    bzip2 \
    ca-certificates \
    locales \
    # - `netbase` provides /etc/{protocols,rpc,services}, part of POSIX
    #   and required by various C functions like getservbyname and getprotobyname
    #   https://github.com/jupyter/docker-stacks/pull/2129
    netbase \
    sudo \
    # - `tini` is installed as a helpful container entrypoint,
    #   that reaps zombie processes and such of the actual executable we want to start
    #   See https://github.com/krallin/tini#why-tini for details
    tini \
    fish \
    curl \
    rsync \
    vim \
    zip \
    unzip \
    git \
    wget \
    apt-utils \
    build-essential \
    # for latex labels
    cm-super \
    dvipng \
    # for matplotlib anim
    ffmpeg \
    fonts-liberation \
    # - `pandoc` is used to convert notebooks to html files
    #   it's not present in the aarch64 Ubuntu image, so we install it here
    pandoc \
    # - `run-one` - a wrapper script that runs no more
    #   than one unique instance of some command with a unique set of arguments,
    #   we use `run-one-constantly` to support the `RESTARTABLE` option
    run-one \
    supervisor \
    gosu \
    openssh-server  && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && \
    echo "en_AYUUTF-8 UTF-8" > /etc/locale.gen && \
    echo "C.UTF-8 UTF-8" >> /etc/locale.gen && \
    mkdir -p /var/run/sshd /var/log/supervisor && \
    locale-gen

# Configure environment
ENV CONDA_DIR=/opt/conda \
    SHELL=/bin/bash \
    USER="${USER}" \
    UID=${UID} \
    GID=${GID} \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    LANGUAGE=C.UTF-8
ENV PATH="${CONDA_DIR}/bin:${PATH}" \
    HOME="/home/${USER}"

# Copy a script that we will use to correct permissions after running certain commands
COPY fix-permissions /usr/local/bin/fix-permissions
RUN chmod a+rx /usr/local/bin/fix-permissions

# Enable prompt color in the skeleton .bashrc before creating the default NB_USER
# hadolint ignore=SC2016
RUN sed -i 's/^#force_color_prompt=yes/force_color_prompt=yes/' /etc/skel/.bashrc

# More information in: https://github.com/jupyter/docker-stacks/pull/2047       # and docs: https://docs.conda.io/projects/conda/en/latest/dev-guide/deep-dives/activation.html
RUN echo 'eval "$(${CONDA_DIR}/bin/conda shell.bash hook)"' >> /etc/skel/.bashrc

# Delete existing user with UID="${UID}" if it exists
# hadolint ignore=SC2046
RUN if grep -q "${UID}" /etc/passwd; then \
        userdel --remove $(id -un "${UID}"); \
    fi

# Create "${USER}" user (`jupyter` by default) with UID="${UID}" (`99` by default) and in the 'users' group
# and make sure these dirs are writable by the `users` group.
RUN echo "auth requisite pam_deny.so" >> /etc/pam.d/su && \
    sed -i.bak -e 's/^%admin/#%admin/' /etc/sudoers && \
    sed -i.bak -e 's/^%sudo/#%sudo/' /etc/sudoers && \
    useradd --no-log-init --create-home --shell /bin/bash --uid "${UID}" --no-user-group "${USER}" && \
    mkdir -p "${CONDA_DIR}" && \
    chown "${USER}:${GID}" "${CONDA_DIR}" && \
    chmod g+w /etc/passwd && \
    fix-permissions "${CONDA_DIR}" && \
    fix-permissions "${HOME}"

# Setup fish shell for root and USER
RUN mkdir -p "${HOME}/.config/fish"
RUN mkdir -p /root/.config/fish
COPY config.fish "${HOME}/.config/fish/config.fish"
COPY config.fish /root/.config/fish
RUN chown $USER:$GROUP "${HOME}/.config/fish/config.fish"

# Change the default shell for both root and the user
RUN chsh -s /usr/bin/fish root \
    && chsh -s /usr/bin/fish $USER

# Setup SSH for key-only access
RUN mkdir -p /var/run/sshd /root/.ssh /etc/ssh && chmod 755 /etc/ssh && \
    echo "PasswordAuthentication no" >> /etc/ssh/sshd_config && \
    echo "PubkeyAuthentication yes" >> /etc/ssh/sshd_config && \
    echo "PermitRootLogin no" >> /etc/ssh/sshd_config && \
    echo "ChallengeResponseAuthentication no" >> /etc/ssh/sshd_config && \
    echo "AuthorizedKeysFile .ssh/authorized_keys" >> /etc/ssh/sshd_config && \
    ssh-keygen -A

RUN chown $USER:$GROUP /etc/ssh/ssh_host*

RUN mkdir -p $HOME/.ssh && \
    chmod 700 $HOME/.ssh

# Copy the authorized_keys files
COPY authorized_keys /home/$USER/.ssh
RUN chmod 600 /home/$USER/.ssh/authorized_keys

# Pin the Python version here, or set it to "default"
ARG PYTHON_VERSION=3.12

# Setup work directory for backward-compatibility
 RUN mkdir "${HOME}/work" && \
     fix-permissions "${HOME}/work"

# Make an empty data processing directory so it is avaliable later
RUN mkdir -p /mnt/data\ processing && \
    fix-permissions /mnt/data\ processing
RUN mkdir -p /mnt/data && \
    fix-permissions /mnt/data
RUN mkdir -p /mnt/code && \
    fix-permissions /mnt/code

# Download and install Micromamba, and initialize the Conda prefix.
COPY --chown="${UID}:${GID}" initial-condarc "${CONDA_DIR}/.condarc"
WORKDIR /tmp
RUN set -x && \
    arch=$(uname -m) && \
    if [ "${arch}" = "x86_64" ]; then \
        # Should be simpler, see <https://github.com/mamba-org/mamba/issues/1437>
        arch="64"; \
    fi && \
    # https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html#linux-and-macos
    wget --progress=dot:giga -O - \
        "https://micro.mamba.pm/api/micromamba/linux-${arch}/latest" | tar -xvj bin/micromamba && \
    PYTHON_SPECIFIER="python=${PYTHON_VERSION}" && \
    if [[ "${PYTHON_VERSION}" == "default" ]]; then PYTHON_SPECIFIER="python"; fi && \
    # Install the packages
    ./bin/micromamba install \
        --root-prefix="${CONDA_DIR}" \
        --prefix="${CONDA_DIR}" \
        --yes \
        'jupyter_core' \
        'conda' \
        'mamba' \
        "${PYTHON_SPECIFIER}" && \
    rm -rf /tmp/bin/ && \
    # Pin major.minor version of python
    # https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-pkgs.html#preventing-packages-from-updating-pinning
    mamba list --full-name 'python' | awk 'END{sub("[^.]*$", "*", $2); print $1 " " $2}' >> "${CONDA_DIR}/conda-meta/pinned" && \
    mamba clean --all -f -y && \
    fix-permissions "${CONDA_DIR}" && \
    fix-permissions "${HOME}"

# Add conda to path for both Bash and Fish
RUN echo 'export PATH=/opt/conda/bin:$PATH' >> /etc/profile && \
    echo 'export PATH=/opt/conda/bin:$PATH' >> /root/.bashrc


USER ${UID}
WORKDIR /home/$USER

RUN chown "${UID}:${GID}" "/home/${USER}/.bashrc" && \
    echo "export PATH=/opt/conda/bin:$PATH" >> "/home/${USER}/.bashrc"

# Install JupyterHub, JupyterLab, NBClassic and Jupyter Notebook
# Generate a Jupyter Server config
# Cleanup temporary files
# Correct permissions
# Do all this in a single RUN command to avoid duplicating all of the
# files across image layers when the permissions change

WORKDIR /tmp
RUN mamba install --yes \
    'jupyterhub-singleuser' \
    'jupyterlab' \
    'nbclassic' \
    'notebook>=7.2.2' \
    'ipykernel' && \
    jupyter server --generate-config && \
    echo "c.PasswordIdentityProvider.hashed_password = 'sha1:41eb0095b22f:18586ae781ed9292674508cdb380469f26a8a1d4'" >> ${HOME}/.jupyter/jupyter_server_config.py && \
    mamba clean --all -f -y && \
    jupyter lab clean && \
    rm -rf "/home/${USER}/.cache/yarn"
    # fix-permissions "${CONDA_DIR}" && \
    # fix-permissions "/home/${USER}"

ENV PATH="${CONDA_DIR}/bin:${PATH}" \
    HOME="/home/${USER}"

USER root
RUN mkdir -p /etc/jupyter

# Fix permissions on /etc/jupyter as root
RUN fix-permissions /etc/jupyter/ && \
    fix-permissions "${CONDA_DIR}" && \
    fix-permissions "${HOME}" && \
    fix-permissions "${CONDA_DIR}" && \
    fix-permissions "/home/${USER}"


RUN chown -R "${USER}:${GROUP}" "${HOME}"

ENV JUPYTER_PORT=8888
EXPOSE $JUPYTER_PORT

WORKDIR "${HOME}"

# Setup supervisor configuration
COPY supervisord.conf.template /etc/supervisor/conf.d/
COPY entrypoint.sh /usr/local/bin/
# Make entrypoint executable
RUN chmod a+rx /usr/local/bin/entrypoint.sh && \
	chown $USER:$GROUP -R /etc/supervisor/ && \
	chown $USER:$GROUP -R /home/$USER

# Set entrypoint and default command
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
