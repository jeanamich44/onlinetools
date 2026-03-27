import paramiko
import io

# ==============================================================================

REMOTE_IP = "137.74.113.52"
REMOTE_USER = "administrator"
REMOTE_PASS = "hJK764TysZVBG1"
REMOTE_FILE_CARDS = r"C:\Users\Administrator\Desktop\BotNVX\.10KSOLO.txt"
REMOTE_FILE_TEST = r"C:\Users\Administrator\Desktop\BotNVX\.test.txt"

# ==============================================================================

def get_ssh_client():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(REMOTE_IP, username=REMOTE_USER, password=REMOTE_PASS, timeout=10)
    return ssh

# ==============================================================================

def fetch_remote_file_content(path):
    ssh = get_ssh_client()
    try:
        sftp = ssh.open_sftp()
        with sftp.open(path, 'r') as f:
            content = f.read().decode('utf-8', errors='ignore')
        sftp.close()
        return content
    finally:
        ssh.close()

# ==============================================================================

def append_lines_remote(path, lines):
    ssh = get_ssh_client()
    try:
        for line in lines:
            cmd = f'powershell -Command "Add-Content -Path \'{path}\' -Value \'{line}\'"'
            ssh.exec_command(cmd)
    finally:
        ssh.close()
