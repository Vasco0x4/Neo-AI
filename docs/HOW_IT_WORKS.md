
## 🛠️  Technical Components

### **Command Execution with `<system>` Tags**

Neo AI uses `<system>` tags to execute Linux commands directly in the terminal. This approach ensures:

- **Controlled Execution**: Only specific commands wrapped in `<system>` tags are executed by the client.

#### **How `<system>` Tags Work**

When Neo identifies a command that needs to be executed, it wraps the command within `<system>` tags to clearly indicate its execution. For example:

- **User Request**: "Neo, can you show me the current directory?"
- **Neo's Response**: "I will execute the following command: `<system>pwd</system>`."

This ensures that Neo's intent is clearly communicated to the server, which processes the command securely.

### **Context Management with `<context>` Tags**

Neo AI maintains an awareness of the user's environment using `<context>` tags. These tags provide information about the current state of the system, such as:

- **Current Directory**: The directory in which the user is currently working.
- **Listed Files**: The files and directories available in the current directory.
- **System Information**: Kernel version, OS details, architecture, and hostname.

#### **How `<context>` Tags Work**

At the beginning of each session or when specific commands are requested, Neo gathers environmental data and wraps it in `<context>` tags. This data is then used to provide more accurate and relevant responses. For example:

```
<context>
Command: pwd
Result:
/home/vasco

Command: ls
Result:
AppImages
Desktop
Documents
Downloads
Music
Pictures
Public
snap
Videos
</context>
```
Neo uses this contextual information to understand the environment and enhance its responses. If a user asks, 

"What files are in my current directory?" 

Neo can immediately refer to the context data and provide an accurate answer without needing to re-execute the command.

### **Asynchronous Command Handling** (Currently in Testing)

For commands expected to take longer than usual (e.g., network scans, file searches, or system updates), Neo AI supports asynchronous execution, allowing:

- **Non-Blocking Interaction**: Users can continue interacting with Neo while a command is processed in the background.
- **Timeout Management**: If a command exceeds a set timeout (e.g., 20 seconds), Neo informs the user that the result will be delivered once it's available.
