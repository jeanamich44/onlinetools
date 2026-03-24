import re
import time
import os
import av
import numpy as np
import noisereduce as nr
import difflib
import paramiko
import json
from faster_whisper import WhisperModel

# CONFIGURATION SERVEUR DISTANT
REMOTE_IP = "137.74.113.52"
REMOTE_USER = "administrator"
REMOTE_PASS = "hJK764TysZVBG1"
REMOTE_FILE = r"C:\Users\Administrator\Desktop\BotNVX\.test.txt"

# ==============================================================================

def send_to_remote_ssh(numbers):
    if not numbers:
        return
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(REMOTE_IP, username=REMOTE_USER, password=REMOTE_PASS, timeout=10)
        
        # On prépare les nombres pour PowerShell (un par ligne)
        # On utilise une boucle simple pour envoyer chaque nombre
        for num in numbers:
            cmd = f'powershell -Command "Add-Content -Path \'{REMOTE_FILE}\' -Value \'{num}\'"'
            ssh.exec_command(cmd)
            
        ssh.close()
        print(f"[SSH] {len(numbers)} nombres envoyés ligne par ligne vers {REMOTE_IP}")
    except Exception as e:
        print(f"[SSH Error] Erreur de connexion ou d'écriture : {str(e)}")

# ==============================================================================

def load_audio_with_av(file_path):
    container = av.open(file_path)
    audio_stream = next(s for s in container.streams if s.type == 'audio')
    resampler = av.AudioResampler(format='s16', layout='mono', rate=16000)
    
    samples = []
    for frame in container.decode(audio_stream):
        resampled_frames = resampler.resample(frame)
        for f in resampled_frames:
            samples.append(f.to_ndarray())
            
    total_samples = np.concatenate(samples, axis=1).reshape(-1).astype(np.float32) / 32768.0
    
    window_size = 16000 * 30 
    for i in range(0, len(total_samples), window_size):
        chunk = total_samples[i:i+window_size]
        peak = np.max(np.abs(chunk))
        if peak > 0.01: 
            total_samples[i:i+window_size] = chunk / peak * 0.90
        
    return total_samples, 16000

# ==============================================================================

def clean_audio_data(y, sr):
    y_clean = nr.reduce_noise(y=y, sr=sr, prop_decrease=0.65, stationary=True)
    return y_clean

# ==============================================================================

def analyze_audio(model, audio_data, beam_size=7, temperature=0.0):
    segments, _ = model.transcribe(
        audio_data,
        beam_size=beam_size,
        temperature=temperature if temperature == 0.0 else [0.0, 0.2, 0.4, 0.6],
        language="fr",
        vad_filter=True,
        vad_parameters=dict(min_speech_duration_ms=400),
        initial_prompt="1, 2, 10, 28, 98, 170, 684, 1110, 2011, 2025. Uniquement des chiffres arabe."
    )
    
    raw_segments = []
    last_text = ""
    for segment in segments:
        text = segment.text.strip()
        if segment.no_speech_prob > 0.60 or segment.avg_logprob < -1.0:
            continue
        if text == last_text or not text:
            continue
        raw_segments.append(text)
        last_text = text
    
    full_text = " ".join(raw_segments)
    full_text = re.sub(r'(\d)\s+(\d)', r'\1\2', full_text)
    
    words = full_text.split()
    numbers = re.findall(r'\d+', full_text)
    
    return {
        "text": full_text,
        "words": words,
        "numbers": numbers,
        "word_count": len(words)
    }

# ==============================================================================

_model_cache = None

def get_model():
    global _model_cache
    if _model_cache is None:
        _model_cache = WhisperModel("small", device="cpu", compute_type="int8")
    return _model_cache

# ==============================================================================

import json

def perform_full_analysis_stream(file_path):
    start_total = time.time()
    model = get_model()
    
    # Étape 1 : Chargement
    step_start = time.time()
    yield json.dumps({"status": "progress", "message": "INITIALISATION : Moteur Whisper chargé.", "step": 1})
    y, sr = load_audio_with_av(file_path)
    elapsed = round(time.time() - step_start, 2)
    yield json.dumps({"status": "progress", "message": f"AUDIO : Signal chargé ({len(y)} samples, {len(y)/sr:.1f}s)", "time": elapsed, "step": 1})
    
    # Étape 2 : Nettoyage
    step_start = time.time()
    yield json.dumps({"status": "progress", "message": "NETTOYAGE : Suppression du bruit de fond (filtre stationnaire)...", "step": 2})
    cleaned_audio = clean_audio_data(y, sr)
    elapsed = round(time.time() - step_start, 2)
    yield json.dumps({"status": "progress", "message": "NETTOYAGE : Bruit réduit et signal normalisé.", "time": elapsed, "step": 2})
    
    # Étape 3 : Pass 1
    step_start = time.time()
    yield json.dumps({"status": "progress", "message": "IA : Lancement du passage 1 (Standard)...", "step": 3})
    res1 = analyze_audio(model, cleaned_audio, beam_size=7, temperature=0.2)
    elapsed = round(time.time() - step_start, 2)
    yield json.dumps({"status": "progress", "message": f"IA : Passage 1 complété ({len(res1['numbers'])} chiffres détectés).", "time": elapsed, "step": 3})
    
    # Étape 4 : Pass 2
    step_start = time.time()
    yield json.dumps({"status": "progress", "message": "IA : Lancement du passage 2 (Haute Précision)...", "step": 4})
    res2 = analyze_audio(model, cleaned_audio, beam_size=10, temperature=0.0)
    elapsed = round(time.time() - step_start, 2)
    yield json.dumps({"status": "progress", "message": f"IA : Passage 2 complété ({len(res2['numbers'])} chiffres détectés).", "time": elapsed, "step": 4})
    
    # Étape 5 : Comparaison
    step_start = time.time()
    yield json.dumps({"status": "progress", "message": "VALIDATION : Comparaison des transcriptions...", "step": 5})
    diff = []
    if res1["text"] != res2["text"] or res1["words"] != res2["words"]:
        ndiff = list(difflib.ndiff(res1["words"], res2["words"]))
        for line in ndiff:
            if line.startswith("- "): diff.append({"type": "pass1_only", "word": line[2:]})
            elif line.startswith("+ "): diff.append({"type": "pass2_only", "word": line[2:]})
    
    res_msg = "Validation réussie : Les passages sont identiques." if not diff else f"Validation : {len(diff)} incohérences trouvées."
    elapsed = round(time.time() - step_start, 2)
    yield json.dumps({"status": "progress", "message": res_msg, "time": elapsed, "step": 5})
    
    # Étape 6 : Transfert SSH
    step_start = time.time()
    if res2["numbers"]:
        numbers_str = ", ".join(res2["numbers"])
        yield json.dumps({"status": "progress", "message": f"SSH : Connexion à {REMOTE_IP} via port 22...", "step": 6})
        
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(REMOTE_IP, username=REMOTE_USER, password=REMOTE_PASS, timeout=10)
            
            yield json.dumps({"status": "progress", "message": f"SSH : Autorisé. Écriture dans {REMOTE_FILE}...", "step": 6})
            
            for num in res2["numbers"]:
                cmd = f'powershell -Command "Add-Content -Path \'{REMOTE_FILE}\' -Value \'{num}\'"'
                ssh.exec_command(cmd)
            
            ssh.close()
            elapsed = round(time.time() - step_start, 2)
            yield json.dumps({"status": "progress", "message": f"SSH : {len(res2['numbers'])} lignes ajoutées avec succès.", "time": elapsed, "step": 6})
        except Exception as e:
            yield json.dumps({"status": "progress", "message": f"SSH ERROR : {str(e)}", "step": 6})
    else:
        yield json.dumps({"status": "progress", "message": "SSH : Aucun nombre trouvé, transfert annulé.", "step": 6})
    
    # Résultat Final
    total_time = round(time.time() - start_total, 2)
    final_res = {
        "pass1": res1,
        "pass2": res2,
        "differences": diff,
        "is_consistent": len(diff) == 0,
        "total_time": total_time
    }
    yield json.dumps({"status": "completed", "results": final_res})

def perform_full_analysis(file_path):
    # Pour garder la compatibilité avec l'ancien code si nécessaire
    gen = perform_full_analysis_stream(file_path)
    final_data = None
    for item in gen:
        data = json.loads(item)
        if data["status"] == "completed":
            final_data = data["results"]
    return final_data

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        res = perform_full_analysis(sys.argv[1])
        print(f"Analyse terminée. Cohérent: {res['is_consistent']}")
        print(f"Passage 1: {res['pass1']['text']}")
        print(f"Passage 2: {res['pass2']['text']}")
    else:
        print("Usage: python audio_analyse.py <file_path>")
