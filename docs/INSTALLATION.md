
#  Neo AI Installation Guide

Welcome to Neo AI ! 

This guide will help you set up Neo AI on both the client and server sides. 



[Video Tutorial](https://youtu.be/on4Cq4G7Uqs)

[![Video Tutorial](https://img.youtube.com/vi/on4Cq4G7Uqs/0.jpg)](https://youtu.be/on4Cq4G7Uqs)


## 🖥️ Client Installation

### Prerequisites

- A Linux-based operating system (Ubuntu, Debian, Fedora, WSL, etc.).
- Python 3.x installed.

### Step 1: Clone the Repository

Start by cloning the Neo AI repository to your local machine:

```bash
git clone https://github.com/Vasco0x4/Neo-AI.git
cd Neo-AI
```

### Step 2: Run the Installation Script

Execute the installation script to set up the environment:

```bash
sudo ./install.sh
```

This script will:

- Create a Python virtual environment.
- Install the necessary Python packages.
- Set up the Neo AI configuration files.
- Add an alias to your `.bashrc` for easy access.

### Step 3: Reload Your Terminal

To apply the changes made by the installation script, restart your terminal or run:

```bash
source ~/.bashrc
```

If Neo AI doesn't work immediately after installation, it may be necessary to add the alias manually. Run the following command inside the Neo AI directory (where `main.py` is located):

```bash
echo "alias neo='source $(pwd)/venv/bin/activate && python3 $(pwd)/main.py'" >> ~/.bashrc
```

## ⚙️ Server Installation

### Prerequisites

Before proceeding with the server installation, ensure that your system meets the following hardware and software requirements:

Linux or Windows
- **Memory**: 16GB+ of RAM is recommended.
- **VRAM**: 6GB+ of VRAM is recommended.  

MacOS

- **M1/M2/M3** with macOS 13.6 or newer.
  

For more information, please refer to the [LM Studio minimum hardware](https://lmstudio.ai/#what-are-the-minimum-hardware-/-software-requirements?).
  
### Step 1: Install LM Studio

1. **Download & Install LM Studio**:

   For Linux, macOS, or Windows, go to the [LM Studio website](https://lmstudio.ai/) and download the latest version compatible with your operating system.

2. **Configure LM Studio**:

   - First, install the desired model in LM Studio (e.g., LLaMA 3.1B is recommended). pre-prompt is designed for LLaMA 3 models.
   - You need to configure the listening Port if not set by default.
   
   ![LM Studio Config](https://github.com/user-attachments/assets/183fa926-a972-4669-93e6-0d5518556455)

   ![LM Studio Config](https://github.com/user-attachments/assets/2417462d-dd2f-4872-a98a-43fbe8d02974)

3. **Set the Pre-Prompt**:

   Copy and paste the Neo Pre-Prompt, which can be found in the [PrePromt.md](../config/PrePromt.md) file.

   ![Pre-Prompt Setup](https://github.com/user-attachments/assets/f7ec4ae0-f1e7-4d73-8e72-1e28463139cf)

4. **Set the Context Length**:

   It is recommended to set the context length between 4000 and 8000 tokens for best results.

   ![Context Setup](https://github.com/user-attachments/assets/ed0f0f13-5f33-4186-a53b-673c7f2c597a)

### Step 2: Test LM Studio Server

Once LM Studio is installed and running, you can test if the server is working properly using the `curl` command. Replace `192.168.0.151` with your actual server IP address.

```bash
curl -X GET http://192.168.0.151:6959/v1/models -H "Content-Type: application/json"
```

If the server is working correctly, you should receive a response.


### Step 3: Configure the `config.yaml` for Neo AI Client

You need to configure the `config.yaml` file on the client side to ensure Neo AI can communicate with the LM Studio server. 

## 🧪 Testing Neo AI

To start Neo AI on the client machine, simply type:

```bash
neo
```

This will launch Neo AI if everything is configured correctly.

### Common Issues

- **Connection Issues**: Verify that the client can reach the server IP and port. Check firewall settings or network configurations if necessary.
- **Dependencies Not Installed**: If dependencies weren’t installed correctly, try deleting the `.venv` folder and rerun the installation script.
- **Voice Commands Not Working**: Run `/docs/testes/test_vocal_device.py` to find the correct microphone index if you're using voice commands.


If you encounter any issues, have questions, or want to provide feedback, feel free to reach out! I'm always happy to help and improve Neo AI

**Discord**: [Vasco0x4]

**Email**: [vasco0x4@proton.me]

---

**Enjoy using Neo AI !**
