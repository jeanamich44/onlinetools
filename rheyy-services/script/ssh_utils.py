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

def fetch_random_lines_remote(path, k):
    ssh = get_ssh_client()
    try:
        # Script PowerShell optimisé pour les gros fichiers : 
        # On cherche des positions d'octets au hasard (Seek) pour éviter de lire tout le fichier.
        # k positions aléatoires -> lecture de la ligne suivante à chaque position.
        ps_script = f"""
        $path = '{path}'
        $k = {k}
        $stream = [System.IO.File]::OpenRead($path)
        $len = $stream.Length
        $results = New-Object System.Collections.Generic.List[string]
        $rand = New-Object System.Random
        
        for ($i=0; $i -lt $k; $i++) {{
            $pos = $rand.NextDouble() * $len
            $stream.Position = [math]::Floor($pos)
            $reader = New-Object System.IO.StreamReader($stream)
            # On ignore la ligne partielle en cours
            $null = $reader.ReadLine()
            # On récupère la ligne complète suivante
            $line = $reader.ReadLine()
            if ($line) {{ $results.Add($line) }}
        }}
        $stream.Close()
        $results
        """
        # On compacte le script pour SSH
        cmd = f'powershell -Command "{ps_script.replace(chr(10), ";").replace(chr(13), "")}"'
        stdin, stdout, stderr = ssh.exec_command(cmd)
        output = stdout.read().decode('utf-8', errors='ignore')
        return [l.strip() for l in output.splitlines() if l.strip()]
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
