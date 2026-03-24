import re
import time
import os
import av
import numpy as np
import noisereduce as nr
import difflib
from faster_whisper import WhisperModel

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

def perform_full_analysis(file_path):
    model = get_model()
    
    y, sr = load_audio_with_av(file_path)
    cleaned_audio = clean_audio_data(y, sr)
    
    res1 = analyze_audio(model, cleaned_audio, beam_size=7, temperature=0.2)
    res2 = analyze_audio(model, cleaned_audio, beam_size=10, temperature=0.0)
    
    diff = []
    if res1["text"] != res2["text"] or res1["words"] != res2["words"]:
        ndiff = list(difflib.ndiff(res1["words"], res2["words"]))
        for line in ndiff:
            if line.startswith("- "):
                diff.append({"type": "pass1_only", "word": line[2:]})
            elif line.startswith("+ "):
                diff.append({"type": "pass2_only", "word": line[2:]})
                
    return {
        "pass1": res1,
        "pass2": res2,
        "differences": diff,
        "is_consistent": len(diff) == 0
    }

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        res = perform_full_analysis(sys.argv[1])
        print(f"Analyse terminée. Cohérent: {res['is_consistent']}")
        print(f"Passage 1: {res['pass1']['text']}")
        print(f"Passage 2: {res['pass2']['text']}")
    else:
        print("Usage: python audio_analyse.py <file_path>")
