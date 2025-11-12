#!/bin/bash
# ===========================================================
#  Client Direct Backup Script (Multiple DB Credentials)
#  No Local Storage — Streams to Backup Server
# ===========================================================

### === CONFIG SECTION === ###
BACKUP_SERVER="Ip address"
BACKUP_USER="root"
BACKUP_PATH="/data/main"
CLIENT_NAME="Youstable"      # Change this per client
SSH_PORT="22"

# List of databases with credentials: "dbname:user:password"
DB_CREDENTIALS=()

# Rotation rules
KEEP_DAILY=7
KEEP_WEEKLY=4
KEEP_MONTHLY=12

# Day definitions
WEEKLY_DAY=7     # Sunday (1=Monday ... 7=Sunday)
MONTHLY_DAY=1    # 1st of month
### === END CONFIG === ###


# ======= SETUP =======
DATE=$(date +%Y-%m-%d)
TIME=$(date +%H%M%S)
DAY_OF_MONTH=$(date +%d)
DAY_OF_WEEK=$(date +%u)
BACKUP_TYPE="daily"

if [[ "$DAY_OF_MONTH" -eq "$MONTHLY_DAY" ]]; then
    BACKUP_TYPE="monthly"
elif [[ "$DAY_OF_WEEK" -eq "$WEEKLY_DAY" ]]; then
    BACKUP_TYPE="weekly"
fi

REMOTE_DIR="$BACKUP_PATH/$CLIENT_NAME/$BACKUP_TYPE/$DATE"

echo "===================================================="
echo "Starting $BACKUP_TYPE backup for $CLIENT_NAME at $(date)"
echo "===================================================="

# ======= CREATE REMOTE DIRECTORY =======
ssh -p "$SSH_PORT" "$BACKUP_USER@$BACKUP_SERVER" "mkdir -p '$REMOTE_DIR/home' '$REMOTE_DIR/databases'"

# ======= /home BACKUP (streamed) =======
echo "[+] Backing up /home directly to remote..."
tar -cpf - /home 2>/dev/null | gzip | ssh -p "$SSH_PORT" "$BACKUP_USER@$BACKUP_SERVER" \
  "cat > '$REMOTE_DIR/home/home-$DATE-$TIME.tar.gz'"
if [[ $? -ne 0 ]]; then
    echo "[-] /home backup failed!"
    exit 1
fi
echo "[✓] /home backup complete"

# ======= DATABASE BACKUPS (streamed) =======
echo "[+] Backing up MySQL databases..."
for entry in "${DB_CREDENTIALS[@]}"; do
    IFS=':' read -r DB USER PASS <<< "$entry"
    echo "    Dumping $DB..."
    mysqldump -u"$USER" -p"$PASS" --single-transaction --quick "$DB" 2>/tmp/db_err.log \
    | gzip | ssh -p "$SSH_PORT" "$BACKUP_USER@$BACKUP_SERVER" \
      "cat > '$REMOTE_DIR/databases/${DB}-$DATE-$TIME.sql.gz'"
    if [[ ${PIPESTATUS[0]} -ne 0 ]]; then
        echo "[-] Failed to dump $DB: $(cat /tmp/db_err.log | tail -1)"
    else
        echo "    [✓] $DB backup complete"
    fi
done
rm -f /tmp/db_err.log


# ======= REMOTE ROTATION =======
echo "[+] Cleaning old backups on backup server..."
ssh -p "$SSH_PORT" "$BACKUP_USER@$BACKUP_SERVER" bash <<EOF
cd "$BACKUP_PATH/$CLIENT_NAME" || exit 0
for t in daily weekly monthly; do
    case \$t in
        daily)   KEEP=$KEEP_DAILY ;;
        weekly)  KEEP=$KEEP_WEEKLY ;;
        monthly) KEEP=$KEEP_MONTHLY ;;
    esac
    [ -d "\$t" ] || continue
    cd "\$t"
    ls -1tr | head -n -\$KEEP | xargs -r rm -rf
    cd ..
done
EOF

echo "[✓] Remote cleanup complete"
echo "===================================================="
echo "Backup completed successfully for $CLIENT_NAME at $(date)"
echo "===================================================="
