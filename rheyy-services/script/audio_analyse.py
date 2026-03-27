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

from script.ssh_utils import append_lines_remote, REMOTE_FILE_TEST

# ==============================================================================

def send_to_remote_ssh(numbers):
    if not numbers:
        return
    try:
        append_lines_remote(REMOTE_FILE_TEST, numbers)
        print(f"[SSH] {len(numbers)} nombres envoyés ligne par ligne.")
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
    yield json.dumps({"status": "progress", "message": "NETTOYAGE : Suppression du bruit de fond...", "step": 2})
    cleaned_audio = clean_audio_data(y, sr)
    elapsed = round(time.time() - step_start, 2)
    yield json.dumps({"status": "progress", "message": "NETTOYAGE : Terminé.", "time": elapsed, "step": 2})
    
    # Étape 3 : Pass 1
    step_start = time.time()
    yield json.dumps({"status": "progress", "message": "IA : Passage 1 (Standard)...", "step": 3})
    res1 = analyze_audio(model, cleaned_audio, beam_size=7, temperature=0.2)
    elapsed = round(time.time() - step_start, 2)
    yield json.dumps({"status": "progress", "message": f"IA : Passage 1 complété ({len(res1['numbers'])} nombres).", "time": elapsed, "step": 3})
    
    # Étape 4 : Pass 2
    step_start = time.time()
    yield json.dumps({"status": "progress", "message": "IA : Passage 2 (Précision)...", "step": 4})
    res2 = analyze_audio(model, cleaned_audio, beam_size=10, temperature=0.0)
    elapsed = round(time.time() - step_start, 2)
    yield json.dumps({"status": "progress", "message": f"IA : Passage 2 complété ({len(res2['numbers'])} nombres).", "time": elapsed, "step": 4})
    
    # Résultat Final (Sans SSH auto)
    total_time = round(time.time() - start_total, 2)
    yield json.dumps({
        "status": "completed", 
        "results": {
            "pass1": res1, "pass2": res2, "total_time": total_time, "is_consistent": res1["text"] == res2["text"]
        }
    })

def perform_retry_analysis_stream(file_path):
    """Analyse avec les paramètres les plus précis possibles pour le modèle Small"""
    start_total = time.time()
    model = get_model()
    
    # Étape 1 : Chargement
    y, sr = load_audio_with_av(file_path)
    cleaned_audio = clean_audio_data(y, sr)
    
    # Étape 2 : Pass 3 (Ultra Précision)
    step_start = time.time()
    yield json.dumps({"status": "progress", "message": "IA ULTRA : Passage 3 (Beam 15, Patience 2.0)...", "step": 1})
    # On force des paramètres plus lourds
    res3 = analyze_audio(model, cleaned_audio, beam_size=15, temperature=0.0) 
    elapsed = round(time.time() - step_start, 2)
    yield json.dumps({"status": "progress", "message": "IA ULTRA : Passage 3 terminé.", "time": elapsed, "step": 1})
    
    # Étape 3 : Pass 4 (Exhaustif)
    step_start = time.time()
    yield json.dumps({"status": "progress", "message": "IA ULTRA : Passage 4 (Final Exhaustif)...", "step": 2})
    res4 = analyze_audio(model, cleaned_audio, beam_size=20, temperature=0.0)
    elapsed = round(time.time() - step_start, 2)
    yield json.dumps({"status": "progress", "message": "IA ULTRA : Passage 4 terminé.", "time": elapsed, "step": 2})
    
    total_time = round(time.time() - start_total, 2)
    yield json.dumps({
        "status": "completed", 
        "results": {
            "pass1": res3, "pass2": res4, "total_time": total_time, "is_consistent": res3["text"] == res4["text"]
        }
    })

def perform_ssh_transfer(numbers):
    """Exécute uniquement le transfert SSH"""
    send_to_remote_ssh(numbers)
    return True

def perform_full_analysis(file_path):
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
