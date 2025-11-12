import paramiko
import yaml
import logging
from datetime import datetime

# Load servers
with open("/opt/automation/main_server/servers.yaml", "r") as f:
    SERVERS = yaml.safe_load(f)["servers"]

LOG_FILE = "/opt/automation/logs/trigger.log"
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s - %(message)s")

def execute_command(ip, command):
    server = next((v for v in SERVERS.values() if v["ip"] == ip), None)
    if not server:
        return f"❌ Server not found for IP: {ip}"

    user = server["user"]
    password = server["password"]

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(ip, username=user, password=password, timeout=30)
        stdin, stdout, stderr = ssh.exec_command(f"bash /automation.sh {command}")
        result = stdout.read().decode()
        error = stderr.read().decode()
        ssh.close()

        msg = f"✅ [{ip}] Executed: {command}\nOutput:\n{result.strip() or 'No output'}"
        if error.strip():
            msg += f"\n⚠️ Errors:\n{error}"
        logging.info(f"{datetime.now()} - {ip} - {command}")
        return msg
    except Exception as e:
        return f"❌ SSH Error on {ip}: {str(e)}"

