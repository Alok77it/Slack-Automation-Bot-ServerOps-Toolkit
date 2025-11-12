import os
import yaml
import paramiko
import logging
import re
import time
import requests
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# ============================================================
# Load environment variables
# ============================================================
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL", "auto-mation")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")  # replace or export

SERVERS_FILE = "/opt/automation/main_server/servers.yaml"
LOG_FILE = "/opt/automation/automation.log"

# ============================================================
# Logging setup
# ============================================================
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# ============================================================
# Slack setup
# ============================================================
app = App(token=SLACK_BOT_TOKEN)
client = WebClient(token=SLACK_BOT_TOKEN)

def slack_send(message, blocks=None):
    """
    Send message using both Web API and fallback webhook.
    """
    try:
        client.chat_postMessage(channel=SLACK_CHANNEL, text=message, blocks=blocks)
    except SlackApiError as e:
        logging.error(f"Slack API error: {e.response['error']}")
        # fallback to webhook
        try:
            requests.post(SLACK_WEBHOOK_URL, json={"text": message})
        except Exception as ex:
            logging.error(f"Webhook fallback failed: {ex}")

# ============================================================
# Helper: Load servers from YAML
# ============================================================
def load_servers():
    try:
        with open(SERVERS_FILE, "r") as f:
            data = yaml.safe_load(f)
        return data.get("servers", {})
    except Exception as e:
        logging.error(f"Error loading servers.yaml: {e}")
        return {}

# ============================================================
# Helper: Execute SSH Command
# ============================================================
def ssh_execute(server_name, action):
    servers = load_servers()
    matched_server = None
    for key in servers.keys():
        if key.lower() == server_name.lower():
            matched_server = key
            break

    if not matched_server:
        return False, f"Server `{server_name}` not found in servers.yaml"

    srv = servers[matched_server]
    ip, user, password = srv["ip"], srv["user"], srv["password"]
    command = f"bash /automation.sh {action}"

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ip, username=user, password=password, timeout=25)

        stdin, stdout, stderr = client.exec_command(command, get_pty=True)
        output = stdout.read().decode("utf-8", errors="replace")
        error = stderr.read().decode("utf-8", errors="replace")
        client.close()

        if error.strip():
            return False, error.strip()
        return True, output.strip()

    except Exception as e:
        return False, f"SSH error: {e}"

# ============================================================
# Slash Command: /server
# ============================================================
@app.command("/server")
def handle_server_command(ack, body, say):
    ack()
    user = body["user_name"]
    text = body.get("text", "")
    msg = f":gear: Received command from *{user}*: `{text}`"
    slack_send(msg)
    logging.info(msg)

    match = re.findall(r"(\w+)=(\S+)", text)
    args = {k.lower(): v for k, v in match}

    server_name = args.get("ip")
    action = args.get("action", "monitor")

    if not server_name:
        slack_send(":x: Missing parameter `ip=`")
        return

    slack_send(f":satellite: Connecting to `{server_name}` for `{action}`...")

    # Progress simulation
    for i in range(1, 7):
        bar = "▰" * i + "▱" * (6 - i)
        slack_send(f"Progress: {bar} {i*16}%")
        time.sleep(0.4)

    success, msg = ssh_execute(server_name, action)
    if success:
        slack_send(f":white_check_mark: Success on `{server_name}`\n```\n{msg}\n```")
        logging.info(f"✅ Success on {server_name}")
    else:
        slack_send(f":x: Failed `{action}` on `{server_name}`\nError:\n```\n{msg}\n```")
        logging.error(f"❌ Failed {action} on {server_name}: {msg}")

# ============================================================
# App startup
# ============================================================
if __name__ == "__main__":
    logging.info("🚀 Starting Slack Handler...")
    print("✅ Slack Automation Bot is running (SocketMode + Webhook enabled)...")

    try:
        SocketModeHandler(app, SLACK_APP_TOKEN).start()
    except Exception as e:
        logging.error(f"Socket Mode failed: {e}")
        print("⚠️ SocketMode failed. Falling back to Webhook-only mode.")
        while True:
            time.sleep(10)

