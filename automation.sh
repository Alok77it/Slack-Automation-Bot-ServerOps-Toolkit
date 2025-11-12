#!/bin/bash
# ===================================================
# UNIVERSAL SERVER AUTOMATION SCRIPT v1.0
# Location: /
# Compatible: Debian, Ubuntu, Fedora, CentOS
# ===================================================

# Detect OS
if [ -f /etc/os-release ]; then
  . /etc/os-release
  OS=$ID
else
  OS=$(uname -s)
fi

# ===== COLORS =====
GREEN="\033[1;32m"
RED="\033[1;31m"
NC="\033[0m"

log() { echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"; }
error() { echo -e "${RED}Error:${NC} $1" >&2; }

case "$1" in
  backup)
    log "Running full backup..."
    bash /backup.sh
    ;;
    
  monitor)
    log "Running system monitor..."
    python3 /monitor.py
    ;;

  health)
    log "Health report:"
    echo "CPU Load: $(uptime | awk -F'load average:' '{ print $2 }')"
    echo "Memory Usage: $(free -m | awk '/Mem:/ {printf("%.2f%"), $3/$2*100}')"
    echo "Disk Usage: $(df -h / | awk 'NR==2{print $5}')"
    ;;

  service)
    SERVICE=$2
    ACTION=$3
    if [[ -z "$SERVICE" || -z "$ACTION" ]]; then
      error "Usage: $0 service <service_name> <start|stop|restart|status>"
      exit 1
    fi
    log "Service $SERVICE → $ACTION"
    systemctl $ACTION $SERVICE
    ;;

  logs)
    FILE=$2
    LINES=${3:-50}
    if [[ -f "$FILE" ]]; then
      tail -n $LINES "$FILE"
    else
      error "Log file not found: $FILE"
    fi
    ;;

  cleanup)
    DAYS=${2:-7}
    log "Cleaning backups older than $DAYS days..."
    find /backup -type f -mtime +$DAYS -delete 2>/dev/null
    ;;

  update)
    MODE=${2:-latest}
    if [[ "$OS" == "debian" || "$OS" == "ubuntu" ]]; then
      log "Detected Debian/Ubuntu"
      apt update -y
      [[ "$MODE" == "latest" ]] && apt upgrade -y
    elif [[ "$OS" == "fedora" || "$OS" == "centos" ]]; then
      log "Detected Fedora/CentOS"
      dnf check-update -y
      [[ "$MODE" == "latest" ]] && dnf upgrade -y
    else
      error "Unsupported OS: $OS"
    fi
    ;;

  install)
    PKG=$2
    VERSION=${3:-latest}
    if [[ -z "$PKG" ]]; then error "Usage: $0 install <pkg> [version]"; exit 1; fi
    log "Installing $PKG version: $VERSION"
    if [[ "$OS" == "debian" || "$OS" == "ubuntu" ]]; then
      [[ "$VERSION" == "latest" ]] && apt install -y $PKG || apt install -y ${PKG}=${VERSION}
    elif [[ "$OS" == "fedora" || "$OS" == "centos" ]]; then
      [[ "$VERSION" == "latest" ]] && dnf install -y $PKG || dnf install -y ${PKG}-${VERSION}
    fi
    ;;

  uptime)
    uptime
    ;;

  audit)
    log "User Audit:"
    lastlog | head -20
    echo "Sudo Users:"
    grep '^sudo:.*$' /etc/group
    ;;

  du)
    log "Top 10 directories consuming space:"
    du -h --max-depth=2 / | sort -hr | head -n 10
    ;;

  firewall)
    ACTION=${2:-status}
    if command -v ufw >/dev/null 2>&1; then
      ufw $ACTION
    elif command -v firewall-cmd >/dev/null 2>&1; then
      firewall-cmd --$ACTION
    else
      error "No firewall system found."
    fi
    ;;

  version)
    log "OS: $PRETTY_NAME"
    log "Script version: 1.0"
    ;;

  *)
    echo "Usage: $0 {backup|monitor|health|service|logs|cleanup|update|install|uptime|audit|du|firewall|version}"
    exit 1
    ;;
esac
