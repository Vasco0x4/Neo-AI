#!/bin/bash

DEBUG=1
function debug() {
    if [ "$DEBUG" -eq 1 ]; then
        echo "DEBUG: $1"
    fi
}

if [[ ! -f "main.py" ]]; then
    echo "The script must be run from the project root containing 'main.py'."
    exit 1
fi

# Function to check if Python version is correct
check_python_version() {
    if command -v python3 &>/dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        debug "Found Python version: $PYTHON_VERSION"
        
        # Use Python for version comparison
        python3 - <<EOF
import sys
if sys.version_info < (3, 6):
    print("Python version 3.6 or higher is required.")
    sys.exit(1)
EOF

        echo "Python version $PYTHON_VERSION is sufficient."
    else
        echo "Python 3 is not installed. Please install Python 3.6 or later."
        exit 1
    fi
}

# Detect package manager and install prerequisites
install_prerequisites() {
    debug "Detecting package manager..."

    if command -v apt &>/dev/null; then
        debug "Using apt package manager"
        sudo apt update
        sudo apt install -y python3-pip python3-venv portaudio19-dev
    elif command -v yum &>/dev/null; then
        debug "Using yum package manager"
        sudo yum install -y python3 python3-pip portaudio-devel
    elif command -v dnf &>/dev/null; then
        debug "Using dnf package manager"
        sudo dnf install -y python3 python3-pip portaudio-devel
    elif command -v zypper &>/dev/null; then
        debug "Using zypper package manager"
        sudo zypper install -y python3 python3-pip portaudio-devel
    elif command -v pacman &>/dev/null; then
        debug "Using pacman package manager"
        sudo pacman -Sy python python-pip portaudio
    else
        echo "Unsupported package manager. Please install Python 3, pip, and venv manually."
        exit 1
    fi
}

# Function to create virtual environment
create_virtualenv() {
    debug "Creating virtual environment..."
    if [[ ! -d "venv" ]]; then
        python3 -m venv venv
        echo "Virtual environment created."
    else
        echo "Virtual environment already exists."
    fi
}

# Function to activate virtual environment
activate_virtualenv() {
    debug "Activating virtual environment..."
    source venv/bin/activate || { echo "Failed to activate virtual environment"; exit 1; }
}

# Function to install required Python packages
install_python_packages() {
    debug "Installing Python packages..."
    cat >requirements.txt <<EOL
setuptools==74.1.2
openai==0.28
pyyaml==6.0.1
speechrecognition==3.10.4
gtts==2.5.3
pynput==1.7.7
PyAudio==0.2.14
EOL

    pip install -r requirements.txt || handle_pyaudio_error
}

# Function to handle PyAudio installation error
handle_pyaudio_error() {
    if [[ $? -ne 0 ]]; then
        echo "PyAudio installation failed. Attempting to install PortAudio and retry..."
        install_prerequisites
        pip install pyaudio
    fi
}

# Function to check installed Python packages
check_python_packages() {
    debug "Checking installed Python packages..."
    REQUIRED_PKG=("setuptools" "openai" "pyyaml" "speechrecognition" "gtts" "pynput" "PyAudio")
    for pkg in "${REQUIRED_PKG[@]}"; do
        if ! pip show $pkg &>/dev/null; then
            echo "Error: $pkg is not installed correctly."
            exit 1
        fi
    done
}

# Function to create persistent memory file
create_persistent_memory() {
    MEMORY_FILE="/tmp/persistent_memory.txt"
    echo "Gathering system information for persistent memory..."
    echo "Kernel Version: $(uname -r)" >$MEMORY_FILE
    echo "OS Info: $(uname -o)" >>$MEMORY_FILE
    echo "Architecture: $(uname -m)" >>$MEMORY_FILE
    echo "Hostname: $(hostname)" >>$MEMORY_FILE
    echo "Persistent memory created in $MEMORY_FILE."
}

# Function to add alias to ~/.bashrc
add_alias_to_bashrc() {
    if ! grep -Fxq "# Neo AI Integration" ~/.bashrc; then
        echo "" >>~/.bashrc
        echo "# Neo AI Integration" >>~/.bashrc
        echo "alias neo='source $(pwd)/venv/bin/activate && python3 $(pwd)/main.py'" >>~/.bashrc
        echo "Alias added to ~/.bashrc"
    else
        echo "Alias already present in ~/.bashrc"
        echo "May be necessary to add it manually."
    fi
}

# Run functions
check_python_version
install_prerequisites
create_virtualenv
activate_virtualenv
install_python_packages
check_python_packages
create_persistent_memory
add_alias_to_bashrc

echo "Installation complete. Please restart your terminal or run 'source ~/.bashrc' to use Neo AI. Enjoy :)"
