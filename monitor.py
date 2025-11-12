#!/usr/bin/env python3
import subprocess, os, shlex, datetime, socket

# ===========================================================
#  Client Monitoring & Backup Verification Script
#  Runs on each client server
#  Backup server: 69.10.34.254 (SSH key-based)
# ===========================================================

# ===== CONFIG =====
CLIENT_NAME = "Youstable"   # Change for each client
BACKUP_SERVER = "Ip address"
BACKUP_USER = "root"
BACKUP_PATH = "/data/main"
SSH_KEY = "~/.ssh/id_ed25519"  # adjust if using another key path

# DATABASES: format name:user:password  (passwords may include ':')
DATABASES = [""]


# ===================


def run_local(cmd):
    """Run a local shell command"""
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = p.communicate()
    return p.returncode, out.strip(), err.strip()


def ssh_remote(cmd):
    """Run a command on the backup server via SSH"""
    ssh = f"ssh -i {os.path.expanduser(SSH_KEY)} -o StrictHostKeyChecking=no -p 22 {BACKUP_USER}@{BACKUP_SERVER}"
    return run_local(f"{ssh} {shlex.quote(cmd)}")


def get_resources():
    """Get CPU, memory, and disk usage"""
    res = {}
    rc, out, _ = run_local("cat /proc/loadavg | awk '{print $1,$2,$3}'")
    res["cpu_load"] = out or "N/A"

    rc, out, _ = run_local("free -m | awk 'NR==2{print $2,$3,$4,$7}'")
    if out:
        total, used, free, avail = out.split()
        res["mem"] = {"total": total, "used": used, "free": free, "avail": avail}
    else:
        res["mem"] = {"total": "0", "used": "0", "free": "0", "avail": "0"}

    rc, out, _ = run_local("df -h /home | awk 'NR==2{print $2,$3,$4,$5}' || df -h / | awk 'NR==2{print $2,$3,$4,$5}'")
    if out:
        size, used, avail, perc = out.split()
        res["disk"] = {"size": size, "used": used, "avail": avail, "perc": perc}
    else:
        res["disk"] = {"size": "N/A", "used": "N/A", "avail": "N/A", "perc": "N/A"}

    return res


def mysql_stats(dbname, user, password):
    """Collect database stats"""
    stats = {"tables": 0, "rows": 0, "columns": 0}
    queries = {
        "tables": f"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='{dbname}';",
        "rows": f"SELECT COALESCE(SUM(TABLE_ROWS),0) FROM information_schema.tables WHERE table_schema='{dbname}';",
        "columns": f"SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='{dbname}';"
    }

    for key, q in queries.items():
        cmd = f"mysql -u{user} -p'{password}' -N -B -e {shlex.quote(q)} 2>/dev/null"
        rc, out, _ = run_local(cmd)
        if rc == 0 and out:
            try:
                stats[key] = int(out.strip())
            except ValueError:
                stats[key] = 0
    return stats


def check_backup(client_name, databases):
    """Verify backup presence and validity on backup server"""
    today = datetime.date.today()
    remote_dirs = [
        f"{BACKUP_PATH}/{client_name}/daily/{today}",
        f"{BACKUP_PATH}/{client_name}/weekly/{today.year}-W{today.isocalendar()[1]:02d}",
        f"{BACKUP_PATH}/{client_name}/monthly/{today.year}-{today.month:02d}"
    ]

    found_dir = None
    for d in remote_dirs:
        rc, _, _ = ssh_remote(f"test -d {shlex.quote(d)}")
        if rc == 0:
            found_dir = d
            break

    if not found_dir:
        return {"found": False, "msg": "No backup directory found"}

    result = {"found": True, "path": found_dir, "home": {}, "dbs": {}}

    # Check /home backup
    rc, out, _ = ssh_remote(f"ls -1t {found_dir}/home/home-*.tar.gz 2>/dev/null | head -n 1")
    if rc == 0 and out:
        f = out.strip()
        rc2, size, _ = ssh_remote(f"stat -c %s {shlex.quote(f)}")
        result["home"] = {"file": f, "size": int(size) if size.isdigit() else 0}
    else:
        result["home"] = {"file": None, "size": 0}

    # Check database backups inside "databases/" directory
    for entry in databases:
        parts = entry.split(":", 2)
        if len(parts) != 3:
            print(f"⚠️  Skipping invalid entry: {entry}")
            continue
        db, user, pw = parts

        remote_db_path = f"{found_dir}/databases"
        rc, out, _ = ssh_remote(f"ls -1t {remote_db_path}/{db}-*.sql.gz 2>/dev/null | head -n 1")

        if rc == 0 and out:
            f = out.strip()
            rc2, size, _ = ssh_remote(f"stat -c %s {shlex.quote(f)}")
            rc3, content, _ = ssh_remote(f"gzip -cd {shlex.quote(f)} | grep -Eic 'create table|insert into'")
            result["dbs"][db] = {
                "file": f,
                "size": int(size) if size.isdigit() else 0,
                "has_data": int(content.strip()) > 0
            }
        else:
            result["dbs"][db] = {"file": None, "size": 0, "has_data": False}

    return result


def print_report():
    """Generate and print system and backup report"""
    hostname = socket.gethostname()
    print(f"\n🔍 SYSTEM REPORT for {CLIENT_NAME} ({hostname}) — {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)

    res = get_resources()
    print(f"CPU Load: {res['cpu_load']}")
    mem = res["mem"]
    print(f"Memory: {mem['used']}/{mem['total']} MB used | Free: {mem['free']} MB | Avail: {mem['avail']} MB")
    disk = res["disk"]
    print(f"/home usage: {disk['used']}/{disk['size']} ({disk['perc']}) available {disk['avail']}")
    print("\n📦 DATABASE DETAILS:")

    total_tables = total_rows = total_cols = 0
    for entry in DATABASES:
        parts = entry.split(":", 2)
        if len(parts) != 3:
            print(f"⚠️  Invalid entry: {entry}")
            continue
        db, user, pw = parts
        stats = mysql_stats(db, user, pw)
        total_tables += stats["tables"]
        total_rows += stats["rows"]
        total_cols += stats["columns"]
        print(f"  {db:<15} ➜ Tables: {stats['tables']:<5} Rows: {stats['rows']:<8} Columns: {stats['columns']:<6}")

    print(f"\n📊 TOTALS ➜ Tables: {total_tables}, Rows: {total_rows}, Columns: {total_cols}")
    print("\n💾 BACKUP VERIFICATION:")

    backup = check_backup(CLIENT_NAME, DATABASES)
    if not backup["found"]:
        print(f"❌ Backup not found: {backup['msg']}")
        return

    print(f"✅ Backup folder: {backup['path']}")
    if backup["home"]["file"]:
        print(f"  /home backup: {backup['home']['file']} ({backup['home']['size']} bytes)")
    else:
        print(f"  ⚠️ /home backup missing!")

    for db, info in backup["dbs"].items():
        if info["file"]:
            status = "✅" if info["has_data"] else "⚠️"
            print(f"  DB {db:<15}: {status} {info['file']} ({info['size']} bytes)")
        else:
            print(f"  ❌ DB {db:<15}: No backup found")

    print("=" * 100)
    print("✔ Report completed.\n")


if __name__ == "__main__":
    print_report()
