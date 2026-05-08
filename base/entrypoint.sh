#!/bin/bash
# entrypoint.sh
set -e

# Default values
DEFAULT_USER="python"
DEFAULT_UID="99"
DEFAULT_GID="100"
DEFAULT_GROUP="users"
CP_OPTS="-a --no-preserve=ownership"

# Get user configuration from environment variables or use defaults
USER_NAME=${USER:-$DEFAULT_USER}
USER_UID=${UID:-$DEFAULT_UID}
USER_GID=${GID:-$DEFAULT_GID}
USER_GROUP=${GROUP:-$DEFAULT_GROUP}
USER_HOME="/home/${USER_NAME}"

# Debug: show environment variables
# echo "USER: ${USER_NAME}"
# echo "HOME_DIR: ${USER_HOME}"
echo "==> Setting up user: $USER_NAME (UID: $USER_UID, GID: $USER_GID)"

# Create/modify group
if getent group $USER_GID >/dev/null; then
    # Group with GID exists, rename it if needed
    EXISTING_GROUP=$(getent group $USER_GID | cut -d: -f1)
    if [ "$EXISTING_GROUP" != "$USER_GROUP" ]; then
        echo "==> Renaming group $EXISTING_GROUP to $USER_GROUP"
        groupmod -n $USER_GROUP $EXISTING_GROUP
    fi
else
    # Create new group
    echo "==> Creating group $USER_GROUP with GID: $USER_GID"
    groupadd -g $USER_GID $USER_GROUP
fi

# Check if USER_NAME exists and has the specified UID and GID
if id -u "$USER_NAME" &>/dev/null; then
    # User exists, now check if UID and GID match
    CURRENT_UID=$(id -u "$USER_NAME")
    CURRENT_GID=$(id -g "$USER_NAME")
    
    if [ "$CURRENT_UID" -eq "$USER_UID" ] && [ "$CURRENT_GID" -eq "$USER_GID" ]; then
        echo "User $USER_NAME already has UID $USER_UID and GID $USER_GID"
    else
        echo "User $USER_NAME exists but with different UID/GID"
        
        # Delete any user with the specified USER_UID (if it's not our target user)
        if getent passwd "$USER_UID" &>/dev/null; then
            USER_WITH_UID=$(getent passwd "$USER_UID" | cut -d: -f1)
            echo "Deleting user $USER_WITH_UID with UID $USER_UID"
            userdel "$USER_WITH_UID"
        fi

        # Now change the UID/GID of the target user
        echo "Changing UID/GID of $USER_NAME to $USER_UID/$USER_GID"
        
        # Get the user's primary group name
        GROUP_NAME=$(id -gn "$USER_NAME")
        
        # Change GID first if needed
        if [ "$CURRENT_GID" -ne "$USER_GID" ]; then
            groupmod -g "$USER_GID" "$GROUP_NAME"
        fi
        
        # Change UID
        if [ "$CURRENT_UID" -ne "$USER_UID" ]; then
            usermod -u "$USER_UID" "$USER_NAME"
        fi

    fi
else
    echo "User $USER_NAME does not exist"
    
    # Delete any user with the specified USER_UID
    if getent passwd "$USER_UID" &>/dev/null; then
        USER_WITH_UID=$(getent passwd "$USER_UID" | cut -d: -f1)
        echo "Deleting user $USER_WITH_UID with UID $USER_UID"
        userdel "$USER_WITH_UID"
    fi

    # Recreate the desired user as we want it
    useradd --no-log-init --home "${USER_HOME}" --shell /bin/bash --uid "${USER_UID}" --gid "${USER_GID}" --groups 100 "${USER_NAME}"
fi

# Rename the default home directory to the desired user's home
# directory if it doesn't already exist, and update the current working
# directory to the new location if needed.
if [[ "${USER_NAME}" != "${DEFAULT_USER}" ]]; then
    # Check if default user's home exists
    if [[ -d "/home/${DEFAULT_USER}" ]]; then
        if [[ ! -e "/home/${USER_NAME}" ]]; then
            # Case 1: Target home doesn't exist yet, simple rename
            echo "Attempting to rename /home/${DEFAULT_USER} to /home/${USER_NAME}..."
            if mv "/home/${DEFAULT_USER}" "/home/${USER_NAME}"; then
                echo "Successfully renamed home directory to /home/${USER_NAME}!"
                # Update passwd entry to point to new home directory
                usermod -d "/home/${USER_NAME}" "${USER_NAME}" 2>/dev/null || true
            else
                echo "Failed to rename /home/${DEFAULT_USER} to /home/${USER_NAME}!"
                # Fallback to the old copy method if rename fails
                echo "Falling back to copy method..."
                mkdir -p "/home/${USER_NAME}"
                shopt -s dotglob  # Enable including hidden files in glob patterns
                if cp ${CP_OPTS:--a} /home/${DEFAULT_USER}/* "/home/${USER_NAME}/" 2>/dev/null; then
                    echo "Successfully copied home directory contents!"
                    shopt -u dotglob  # Disable the dotglob option when done
                else
                    echo "Failed to copy data from /home/${DEFAULT_USER} to /home/${USER_NAME}!"
                    echo "Attempting to symlink /home/${DEFAULT_USER} to /home/${USER_NAME}..."
                    # Remove the potentially empty directory created by failed copy
                    rmdir "/home/${USER_NAME}" 2>/dev/null || true
                    if ln -s /home/${DEFAULT_USER} "/home/${USER_NAME}"; then
                        echo "Success creating symlink!"
                    else
                        echo "ERROR: All methods failed! Could not set up /home/${USER_NAME}!"
                        exit 1
                    fi
                fi
            fi
        else
            # Case 2: Both directories exist, need to merge them
            echo "Both /home/${DEFAULT_USER} and /home/${USER_NAME} exist. Merging contents..."
            # Create temporary directory for merging
            TMP_DIR=$(mktemp -d)
            # Enable dotglob for hidden files
            shopt -s dotglob
            
            # Copy all content from DEFAULT_USER to temp dir
            if cp ${CP_OPTS:--a} /home/${DEFAULT_USER}/* "${TMP_DIR}/" 2>/dev/null; then
                # Copy from temp to USER_NAME, preserving existing files in USER_NAME
                if cp -n ${CP_OPTS:--a} "${TMP_DIR}"/* "/home/${USER_NAME}/" 2>/dev/null; then
                    echo "Successfully merged home directories!"
                    # Clean up temp directory
                    rm -rf "${TMP_DIR}"
                    # Clean up default directory 
                    rm -rf "/home/${DEFAULT_USER}"
                    # Update passwd entry to ensure it points to new home
                    usermod -d "/home/${USER_NAME}" "${USER_NAME}" 2>/dev/null || true
                else
                    echo "ERROR: Failed to merge directories!"
                    exit 1
                fi
            else
                echo "ERROR: Failed to copy files to temporary location!"
                exit 1
            fi
            
            # Disable dotglob when done
            shopt -u dotglob
        fi
    else
        echo "Default home directory /home/${DEFAULT_USER} does not exist. No action needed."
    fi
    
    # Ensure the current working directory is updated to the new path
    if [[ "${PWD}/" == "/home/${DEFAULT_USER}/"* ]]; then
        new_wd="/home/${USER_NAME}/${PWD:13}"
        echo "Changing working directory to ${new_wd}"
        _cd_ "${new_wd}"
    fi
fi

USER_HOME="/home/${USER_NAME}"
HOME="/home/${USER_NAME}"
cd "${HOME}"

# Fix permissions for any known directories that need to be writable by the user
# Modify this section based on your specific needs
for DIR in $CONDA_DIR $USER_HOME "/run" ; do
    if [ -d "$DIR" ]; then
        echo "==> Ensuring $USER_NAME has permissions on $DIR"
        fix-permissions $DIR
    fi
done

# Home directory needs direct ownership though
chown -R "${USER_UID}:${USER_GID}" "$USER_HOME"

# Clean any installs
mamba clean --all -f -y && \
jupyter lab clean && \
rm -rf "${USER_HOME}/.cache/yarn" && \

# Generate supervisor config with the correct username
# echo "Generating supervisord.conf from template..."
sed "s|%%USER_NAME%%|${USER_NAME}|g; s|%%HOME_DIR%%|${USER_HOME}|g" \
    /etc/supervisor/conf.d/supervisord.conf.template > /etc/supervisor/conf.d/supervisord.conf

# Debug: show the generated config
# echo "Generated supervisord.conf content:"
# cat /etc/supervisor/conf.d/supervisord.conf

# Set fish as the user shell 
chsh -s /usr/bin/fish $USER

# If this script is run as the entrypoint and a command was specified,
# switch to the user and execute the command
if [ $# -gt 0 ]; then
    echo "==> Executing command as $USER_NAME: $@"
    exec gosu $USER_NAME "$@"
else
    # If no command was provided, default to bash
    echo "==> No command provided, starting bash as $USER_NAME"
    exec gosu $USER_NAME /bin/bash
fi
