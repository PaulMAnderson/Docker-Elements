#!/usr/bin/env fish

# Skip configuration for non-interactive shells
if not status is-interactive
    exit
end

# History configuration
set -g fish_history_control ignoreboth
set -g fish_history save  # Equivalent to histappend
set -g HISTSIZE 1000  
set -g fish_history_max_in_file 2000  # Equivalent to HISTFILESIZE

# Less configuration
if test -x /usr/bin/lesspipe
    set -gx LESSOPEN "| /usr/bin/lesspipe %s"
    set -gx LESSCLOSE "/usr/bin/lesspipe %s %s"
end

# Chroot detection
set -g debian_chroot ""
if test -z "$debian_chroot"; and test -r /etc/debian_chroot
    set debian_chroot (cat /etc/debian_chroot)
end

# Color settings - Catpuccin
# url: 'https://github.com/catppuccin/fish'
# preferred_background: 24273a

set -g fish_color_normal cad3f5
set -g fish_color_command 8aadf4
set -g fish_color_param f0c6c6
set -g fish_color_keyword ed8796
set -g fish_color_quote a6da95
set -g fish_color_redirection f5bde6
set -g fish_color_end f5a97f
set -g fish_color_comment 8087a2
set -g fish_color_error ed8796
set -g fish_color_gray 6e738d
set -g fish_color_selection --background=363a4f
set -g fish_color_search_match --background=363a4f
set -g fish_color_option a6da95
set -g fish_color_operator f5bde6
set -g fish_color_escape ee99a0
set -g fish_color_autosuggestion 6e738d
set -g fish_color_cancel ed8796
set -g fish_color_cwd eed49f
set -g fish_color_user 8bd5ca
set -g fish_color_host 8aadf4
set -g fish_color_host_remote a6da95
set -g fish_color_status ed8796
set -g fish_pager_color_progress 6e738d
set -g fish_pager_color_prefix f5bde6
set -g fish_pager_color_completion cad3f5
set -g fish_pager_color_description 6e738d


# Custom prompt with chroot support
function fish_prompt
    set -l last_status $status
    
    # Chroot display
    if test -n "$debian_chroot"
        echo -n "($debian_chroot)"
    end
    
    # User and host
    set_color $fish_color_user
    echo -n (whoami)
    set_color normal
    echo -n "@"
    set_color $fish_color_host
    echo -n (hostname -s)
    set_color normal
    
    echo -n ":"
    
    # Current directory
    set_color $fish_color_cwd
    echo -n (prompt_pwd)
    set_color normal
    
    # Prompt character
    echo -n '$ '
end

# Set terminal title
function fish_title
    if test -n "$debian_chroot"
        echo "$debian_chroot"(whoami)'@'(hostname)': '(prompt_pwd)
    else
        echo (whoami)'@'(hostname)': '(prompt_pwd)
    end
end

# Alias definitions for color support
if type -q dircolors
    if test -r ~/.dircolors
        eval (dircolors -c ~/.dircolors | sed 's/>&\/dev\/null$//')
    else
        eval (dircolors -c | sed 's/>&\/dev\/null$//')
    end
    
    # Color aliases
    alias ls='ls --color=auto'
    alias grep='grep --color=auto'
    alias fgrep='fgrep --color=auto'
    alias egrep='egrep --color=auto'
end

# ls aliases
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'

# Alert alias
function alert
    set -l status_face (test $status = 0; and echo "terminal"; or echo "error")
    set -l last_cmd (history | head -n1 | string replace -r '^\s*\d+\s+' '' | string replace -r '[;&|]\s*alert$' '')
    notify-send --urgency=low -i $status_face "$last_cmd"
end

# Load external aliases file if it exists
if test -f ~/.config/fish/aliases.fish
    source ~/.config/fish/aliases.fish
end

# Function to initialize conda in fish
function conda_init
    # Configure conda for fish
    eval /opt/conda/bin/conda "shell.fish" "hook" | source
    # Initialize conda-libmamba solver if installed
    if type -q mamba
        conda config --set solver libmamba
    end
end

# Shortcut for conda activation
alias activate="conda activate"

conda_init

umask 002

