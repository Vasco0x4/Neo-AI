# Neo AI - Your Linux Terminal Assistant

Neo is an AI assistant designed to enhance your Linux terminal experience. It understands command context, executes Linux commands securely, and assists with cybersecurity tasks including network scanning and CTF challenges.


## 🎥 **Demo**

[Coming soon]

## 🔧 **How It Works**

Neo operates through a system of tags and contextual awareness that allows it to interact with your Linux environment.

---

### **Command Processing**

Neo uses two primary tag types for system interaction:

- **`<system>` Tags**: These tags enable Neo to execute commands.
  ```markdown
  User: Show me the current directory
  <system>pwd</system>
  ```

- **`<context>` Tags**: System context.
  ```markdown
  <context>
  Current Directory: /home/user
  Files: Documents, Downloads, Pictures, shell.php
  System: Ubuntu 22.04, Kernel 5.15
  </context>
  ```

---

### **System Interaction**

At each session launch, Neo automatically gathers system information such as:

- System information:
  ```markdown
  Kernel Version: 6.8.0-49-generic
  OS Info: Linux
  Architecture: x86_64
  Hostname: vasco
  ```
- Current directory location (`pwd`)
- Available files and directories (`ls -a`)

**Customization:** You can add more commands to the context section by simply appending them to the script. Neo will execute them automatically and send the results back with the `<system>` tag.

---

### Example Interaction

![image](https://github.com/user-attachments/assets/150653e5-7234-4f84-b67d-6a51e5202e3d)


**Approval Process:**  
The user must approve each command before execution

After execution, the output is displayed in a new GNOME window or prompts for sudo if required

![image](https://github.com/user-attachments/assets/70445b99-2dac-46b4-8cef-fb08c38bdbf5)

The output command will be automatically sent to Neo

![image](https://github.com/user-attachments/assets/8e2ad972-617b-4fb7-8fe0-8f6c5c482173)

If further investigation is needed Neo will ask you for execute another command

![image](https://github.com/user-attachments/assets/31da3517-115d-4a76-b910-8a957095a93a)

In this way, Neo can interact with Linux with system tags. The possibilities are infinite! You can use it when you forget simple commands or need to analyze files, perform DNS forensics, or do anything on Linux. :)

## ⚙️ **Server Options**

Currently, Neo requires a server to function. You can use either:

1. **LM Studio** (local installation)
2. **DigitalOcean API Key** (recommended)

Future compatibility with other APIs is under development.

> I will develop new compatibility, but it takes time. Every API has a different approach to chat, streaming, etc.


## 🛠️ **Installation**

For detailed installation instructions:

[Installation Guide](./docs/INSTALLATION.md)

## 📜 **License**

BSD 3-Clause License

> *Friendly tip:* Don't insult Neo—it might shut down your computer! Good luck!
