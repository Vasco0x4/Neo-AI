# Neo AI Installation Guide

Welcome to Neo AI ! This guide will help you set up Neo AI with either LM Studio or DigitalOcean.

## 🖥️ Client Installation

### Basic Setup

```bash
git clone https://github.com/Vasco0x4/Neo-AI.git
cd Neo-AI
sudo ./install.sh
source ~/.bashrc
```

If needed, add the alias manually:
```bash
echo "alias neo='source $(pwd)/venv/bin/activate && python3 $(pwd)/main.py'" >> ~/.bashrc
```
and start new terminal.

## ⚙️ Server Options

### Option 1: LM Studio Setup

1. **Download & Install**
   - Get LM Studio from [lmstudio.ai](https://lmstudio.ai/)
   - Install your preferred model (LLaMA 3.2B recommended)

2. **Server Configuration**
   - Set listening port (default: 6959)
   - Configure context length (6000-10000 tokens)
   - Import Neo Pre-Prompt from `config/PrePrompt.md`

3. **Test Connection**
```bash
curl -X GET http://YOUR_IP:6959/v1/models -H "Content-Type: application/json"
```

### Option 2: DigitalOcean Setup

1. **Create Agent**
   - Access DigitalOcean GenAI
   - Create new AI agent
   - Import Neo Pre-Prompt from `config/PrePrompt.md`
   
2. **Update Config**
   - Modify `config.yaml`:
```yaml
mode: "digital_ocean"
digital_ocean:
  agent_id: "your-agent-id"
  agent_key: "your-agent-key"
  agent_endpoint: "your-endpoint"
```

## 🧪 Testing Neo AI


To start Neo AI, simply type `neo` wherever you need.

![Usage example](./assets/Hello_neo.gif)

**Enjoy using Neo AI!**
