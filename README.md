# 🤖 **Slack Automation Bot — ServerOps Toolkit**  
*Supercharge your server management from Slack. Real-time DevOps, at your command!* 🚀

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8%2B-blue?logo=python" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/slack-api-5D3FD3?logo=slack" alt="Slack API">
  <img src="https://img.shields.io/github/license/Alok77it/Slack-Automation-Bot-ServerOps-Toolkit?color=green" alt="License">
</p>

---

## 📦 Overview

Manage, monitor, and automate your Linux servers straight from your Slack workspace!  
**Slack Automation Bot — ServerOps Toolkit** empowers DevOps teams and sysadmins to securely orchestrate operations across multiple servers through intuitive Slack commands. No context-switching. No hassle. Just **Ops — made easy.** 💼

> **Integrated with Slack | Lightweight Python & Shell | Secure, Audit-Ready Operations**

---

## ⚙️ Features

| 🚀 Feature                  | 💡 Description                                                    | 🔗 Command Syntax                                   |
|-----------------------------|-------------------------------------------------------------------|-----------------------------------------------------|
| :chart_with_upwards_trend:  | System Health Monitoring                                         | `/server ip=192.168.1.5 action=monitor`             |
| :floppy_disk:               | Backups & Updates                                                | `/server ip=prod-db action=backup`                  |
| :mag_right:                 | Check Services, Uptime, Logs                                     | `/server ip=web-01 action=status`                   |
| :scroll:                    | Fetch Real-time System Logs                                      | `/server ip=app-02 action=logs`                     |
| :gear:                      | Execute Remote Custom Scripts                                    | `/server ip=stage-03 action=script script=deploy.sh`|
| :speech_balloon:            | Slack-Embedded Notifications & Summaries                         | (Automated in `#auto-mation` channel)               |
| :lock:                      | Secure, Auditable Communication                                 | All interactions logged & validated                 |

---

## <img src="https://raw.githubusercontent.com/Alok77it/Slack-Automation-Bot-ServerOps-Toolkit/main/serverops-animated-demo.svg" width="60%" alt="ServerOps Animation">

_**See the bot in action!**_  
_Animated interaction: Slack command triggers server health check and posts real-time stats and logs to <code>#auto-mation</code>_

---

## 🚀 Installation

```bash
# 1. Clone the repo
git clone https://github.com/Alok77it/Slack-Automation-Bot-ServerOps-Toolkit.git
cd Slack-Automation-Bot-ServerOps-Toolkit

# 2. Create and activate a Python virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your environment variables (.env file or export)
# SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET, etc.

# 5. Start the bot
python main.py
```

---

## 💬 Slack Setup Guide

> **⚠️ Prerequisite:** _You must be a Slack workspace admin to create bots and configure permissions._

1. **Create a Slack App:**  
   - Go to [Slack API Apps](https://api.slack.com/apps) &rarr; _Create New App_
   - Choose "From scratch," name your bot, and assign to the correct workspace.

2. **Configure Bot Scopes:**  
   - _Recommended scopes_: `chat:write`, `commands`, `channels:read`, `users:read`, `groups:read`
   - Add **Slash Command(s)**: `/server`, `/serverops` etc.

3. **Install App to Workspace:**  
   - Install the app, granting the necessary permissions.

4. **Set Secrets & Tokens:**  
   - Obtain `SLACK_BOT_TOKEN` and `SLACK_SIGNING_SECRET`.
   - Store them in your environment as per installation instructions.

5. **Invite the bot to your channel:**  
   - `/invite @YourBotName` in `#auto-mation`

> ✅ **Tip:** Name your automation channel `#auto-mation` for unified ops visibility!

---

## 🧠 Usage Examples

Command structure:  
```shell
/server ip=<host/ip/alias> action=<action> [script=<script_name>]
```

**Examples:**
```shell
/server ip=prod-db action=backup
/server ip=web-01 action=monitor
/server ip=app-02 action=logs
/server ip=stage-03 action=script script=cleanup.sh
```

_Bot will reply instantly in the channel with updates, logs, and results!_

---

## 🧾 Logging Details

All commands and responses are logged for **auditability** & **security**.  
Logs recorded:
- Slack user, timestamp, command issued
- Server addressed & action taken
- Result (success/error) & bot output

> 🔒 **Note:** Logs are stored securely in `/logs/` (configurable). Regular review is recommended for enterprise use.

---

## 🧱 Directory Structure

```
/
├── main.py                # Bot entrypoint
├── commands.py            # Slack commands, event handlers
├── monitor.py             # SSH, server monitoring actions
├── backup.py              # Backup and update tasks
├── utils.py               # Utilities for all ops
├── scripts/               # Shell scripts for server ops
├── logs/                  # Operation, error, and audit logs
├── requirements.txt
└── README.md
```

---

## 🧑‍💻 Contributing

We welcome PRs, issues, and enhancements!  
- 🚩 Fork the repo & clone locally.
- 🔃 Create a new branch for your feature/fix.
- 🛠️ Ensure code follows project style & passes checks.
- 📬 Open your Pull Request and let's improve ServerOps together!

---

> _Made with 🐍 Python & 🛠️ Shell. Designed for busy DevOps by [Alok77it](https://github.com/Alok77it)._

```
⚠️
**Security Best Practice:** _Never expose your credentials in code or screenshots! Always use environment variables for secrets._
```
