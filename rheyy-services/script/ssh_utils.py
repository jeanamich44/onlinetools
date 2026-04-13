import paramiko
import io

# ==============================================================================

REMOTE_IP = "137.74.113.52"
REMOTE_USER = "administrator"
REMOTE_PASS = "hJK764TysZVBG1"
REMOTE_FILE_CARDS = r"C:\Users\Administrator\Desktop\BotNVX\.10KSOLO.txt"
REMOTE_FILE_TEST = r"C:\Users\Administrator\Desktop\BotNVX\.test.txt"
REMOTE_FILE_DATA = r"C:\Users\Administrator\Desktop\BotNVX\data.txt"
REMOTE_FILE_DBFLUNCH = r"C:\Users\Administrator\Desktop\BotNVX\dbflunch.txt"
REMOTE_BOT_EXE = r"C:\Users\Administrator\Desktop\BotNVX\main.exe"
REMOTE_BOT_DIR = r"C:\Users\Administrator\Desktop\BotNVX"

# ==============================================================================

import random

import base64

def fetch_random_lines_remote(path, k):
    ssh = get_ssh_client()
    try:
        # Script PowerShell robuste avec gestion propre du flux
        ps_script = f"""
        $path = "{path}"
        $k = {k}
        try {{
            $stream = [System.IO.File]::OpenRead($path)
            $len = $stream.Length
            $rand = New-Object System.Random
            for ($i=0; $i -lt $k; $i++) {{
                $pos = [int64]($rand.NextDouble() * ($len - 1024))
                if ($pos -lt 0) {{ $pos = 0 }}
                $stream.Position = $pos
                $reader = New-Object System.IO.StreamReader($stream)
                $null = $reader.ReadLine()
                $line = $reader.ReadLine()
                if ($line) {{ $line }}
            }}
            $stream.Close()
        }} catch {{
            $_.Exception.Message
        }}
        """
        # Encodage Base64 (UTF-16LE requis par PowerShell -EncodedCommand)
        encoded_script = base64.b64encode(ps_script.encode('utf-16-le')).decode('ascii')
        cmd = f'powershell -EncodedCommand {encoded_script}'
        
        stdin, stdout, stderr = ssh.exec_command(cmd)
        output = stdout.read().decode('utf-8', errors='ignore')
        
        lines = [l.strip() for l in output.splitlines() if l.strip()]
        return lines
    finally:
        ssh.close()

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
    if not lines: return
    ssh = get_ssh_client()
    try:
        content = "`n".join(lines) 
        cmd = f'powershell -Command "Add-Content -Path \'{path}\' -Value \'{content}\'"'
        ssh.exec_command(cmd)
    finally:
        ssh.close()

# ==============================================================================

def write_remote_file(path, content):
    """Écrase le fichier distant avec le nouveau contenu via SFTP en UTF-8"""
    ssh = get_ssh_client()
    try:
        sftp = ssh.open_sftp()
        with sftp.file(path, 'w') as f:
            f.write(content.encode('utf-8'))
        sftp.close()
    finally:
        ssh.close()

def run_remote_bot():
    """Lance l'exécutable distant de façon persistante"""
    ssh = get_ssh_client()
    try:
        # Utilisation de Start-Process pour que le bot survive à la déconnexion SSH
        # Et guillemets autour des chemins pour supporter les espaces
        cmd = f'powershell -Command "cd \'{REMOTE_BOT_DIR}\'; Start-Process \'{REMOTE_BOT_EXE}\'"'
        ssh.exec_command(cmd)
    finally:
        ssh.close()
