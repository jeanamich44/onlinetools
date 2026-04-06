from fastapi import FastAPI, HTTPException, Request, Depends, Body, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import time
import logging
import json
import uuid
import shutil
import os
import subprocess

from script.database import init_db, get_db, Payment, Admin, Setting
from script.security import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    get_current_admin,
    check_ip_whitelist
)
from script.mrz import generate_mrz, generate_random_data
from script.qr_zip import generate_qr_zip
from script.packager import generate_packaging_elite
from script.audio_analyse import (
    perform_full_analysis, 
    perform_full_analysis_stream, 
    perform_retry_analysis_stream
)
from script.ssh_utils import (
    fetch_remote_file_content, 
    get_ssh_client, 
    REMOTE_FILE_CARDS,
    write_remote_file,
    run_remote_bot,
    REMOTE_FILE_DATA
)

# [ CONFIGURATION ] ============================================================

app = FastAPI(title="Rheyy Services", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

audio_files = {}

# [ TOOLS - PACKAGER ] =========================================================

@app.get("/tools/packager-index")
async def get_packager_index(db: Session = Depends(get_db), admin: str = Depends(get_current_admin)):
    setting = db.query(Setting).filter(Setting.key == "packager_index").first()
    if not setting:
        return {"index": 1}
    return {"index": int(setting.value)}

@app.patch("/tools/packager-index")
async def update_packager_index(data: dict = Body(...), db: Session = Depends(get_db), admin: str = Depends(get_current_admin)):
    new_index = data.get("index")
    if new_index is None:
        raise HTTPException(status_code=400, detail="Index manquant")
    setting = db.query(Setting).filter(Setting.key == "packager_index").first()
    if not setting:
        setting = Setting(key="packager_index", value=str(new_index))
        db.add(setting)
    else:
        setting.value = str(new_index)
    db.commit()
    return {"status": "success", "index": new_index}

@app.post("/generate-pack")
async def generate_pack_endpoint(request: Request, bg: BackgroundTasks, db: Session = Depends(get_db), admin: str = Depends(get_current_admin)):
    form_data = await request.form()
    source = form_data.get("source", "upload")
    form_start = form_data.get("start_line")
    title = form_data.get("title")
    
    setting = db.query(Setting).filter(Setting.key == "packager_index").first()
    if not setting:
        setting = Setting(key="packager_index", value="1")
        db.add(setting)
        db.commit()
    
    if form_start and str(form_start).strip().isdigit():
        start_line = max(1, int(form_start))
    else:
        start_line = max(1, int(setting.value))
    
    lines = []
    try:
        if source == "remote":
            content = fetch_remote_file_content(REMOTE_FILE_CARDS)
            lines = content.splitlines()
        else:
            file = form_data.get("file")
            if not file:
                raise HTTPException(status_code=400, detail="Fichier texte manquant")
            content = await file.read()
            lines = content.decode("utf-8", errors="ignore").splitlines()
        
        lines = [l.strip() for l in lines if l.strip()]
        
        if len(lines) < start_line:
            raise HTTPException(status_code=400, detail=f"Index de départ ({start_line}) trop élevé.")
            
        final_zip = generate_packaging_elite(lines, start_line - 1, title)
        setting.value = str(start_line + 200)
        db.commit()
        bg.add_task(os.remove, final_zip)
        return FileResponse(final_zip, media_type="application/zip", filename=f"pack_200_line_{start_line}.zip")
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# [ TOOLS - SSH ] ==============================================================

@app.get("/tools/fetch-remote-cards")
async def fetch_remote_cards_endpoint(admin: str = Depends(get_current_admin)):
    try:
        ssh = get_ssh_client()
        sftp = ssh.open_sftp()
        stat = sftp.stat(REMOTE_FILE_CARDS)
        sftp.close()
        ssh.close()
        return {"status": "available", "size": stat.st_size}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SSH Check Error: {str(e)}")

# [ AUDIO ANALYSE ] ============================================================

@app.post("/analyze-audio-stream")
async def analyze_audio_streaming_endpoint(request: Request, admin: str = Depends(get_current_admin)):
    form_data = await request.form()
    file = form_data.get("file")
    if not file:
        raise HTTPException(status_code=400, detail="Fichier manquant")
        
    file_id = str(uuid.uuid4())
    temp_path = f"audio_{file_id}_{file.filename}"
    audio_files[file_id] = temp_path
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    async def event_generator():
        for progress_json in perform_full_analysis_stream(temp_path):
            data = json.loads(progress_json)
            if data["status"] == "completed":
                data["file_id"] = file_id
                yield json.dumps(data) + "\n"
            else:
                yield progress_json + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")

@app.post("/analyze-audio-retry")
async def analyze_audio_retry_endpoint(req: dict = Body(...), admin: str = Depends(get_current_admin)):
    file_id = req.get("file_id")
    temp_path = audio_files.get(file_id)
    if not temp_path or not os.path.exists(temp_path):
        raise HTTPException(status_code=404, detail="Fichier audio expiré ou introuvable.")
        
    async def event_generator():
        for progress_json in perform_retry_analysis_stream(temp_path):
            yield progress_json + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")

@app.post("/analyze-audio-cleanup")
async def analyze_audio_cleanup_endpoint(req: dict = Body(...), admin: str = Depends(get_current_admin)):
    file_id = req.get("file_id")
    temp_path = audio_files.pop(file_id, None)
    
    if temp_path and os.path.exists(temp_path):
        os.remove(temp_path)
        
    return {"status": "success", "message": "Fichier temporaire nettoyé."}

@app.post("/analyze-audio-matcher")
async def analyze_audio_matcher_endpoint(request: Request, admin: str = Depends(get_current_admin)):
    form_data = await request.form()
    audio_file = form_data.get("audio")
    txt_file = form_data.get("txt")
    
    if not audio_file or not txt_file:
        raise HTTPException(status_code=400, detail="Fichiers manquants (Audio + TXT requis)")
    
    # Lecture du TXT
    txt_content = await txt_file.read()
    card_lines = txt_content.decode("utf-8", errors="ignore").splitlines()
    card_lines = [l.strip() for l in card_lines if l.strip()]
    
    file_id = str(uuid.uuid4())
    temp_path = f"audio_matcher_{file_id}_{audio_file.filename}"
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(audio_file.file, buffer)
        
    async def event_generator():
        try:
            for progress_json in perform_full_analysis_stream(temp_path):
                data = json.loads(progress_json)
                if data["status"] == "completed":
                    found_soldes = data["results"]["pass2"]["numbers"]
                    
                    # Validation Dynamique : TXT == Audio
                    if len(card_lines) != len(found_soldes):
                        yield json.dumps({
                            "status": "error", 
                            "message": f"Divergence détectée : {len(card_lines)} cartes attendues, mais {len(found_soldes)} soldes trouvés par l'IA."
                        }) + "\n"
                        return

                    final_list = []
                    for i in range(len(card_lines)):
                        final_list.append(f"{card_lines[i]} = {found_soldes[i]}")

                    data["matched_results"] = final_list
                    data["file_id"] = file_id
                    yield json.dumps(data) + "\n"
                else:
                    yield progress_json + "\n"
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")

@app.post("/analyze-audio-matcher-confirm")
async def analyze_audio_matcher_confirm_endpoint(req: dict = Body(...), admin: str = Depends(get_current_admin)):
    results = req.get("results", [])
    if not results:
        raise HTTPException(status_code=400, detail="Aucun résultat à envoyer")
        
    try:
        final_content = "\n".join(results)
        write_remote_file(REMOTE_FILE_DATA, final_content)
        run_remote_bot()
        return {"status": "success", "message": "Liste envoyée et bot lancé avec succès !"}
    except Exception as ssh_err:
        raise HTTPException(status_code=500, detail=f"Erreur SSH : {str(ssh_err)}")

# [ FLUNCH ] ===================================================================

@app.get("/admin/flunch/files")
async def get_flunch_files(admin: str = Depends(get_current_admin)):
    base_flunch = os.path.join("script", "flunch")
    files = {
        "automation": os.path.join(base_flunch, "logs", "automation.log"),
        "mails": os.path.join(base_flunch, "output", "mails_recus.txt"),
        "token": os.path.join(base_flunch, "output", "bearer_token.txt")
    }
    
    results = {}
    for key, path in files.items():
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                results[key] = f.read()
        else:
            results[key] = ""
            
    return results

@app.get("/admin/flunch/screenshot")
async def get_flunch_screenshot(admin: str = Depends(get_current_admin)):
    path = os.path.join("script", "flunch", "output", "screenshot.png")
    if os.path.exists(path):
        return FileResponse(path, media_type="image/png")
    raise HTTPException(status_code=404, detail="Capture d'écran non disponible")
    
@app.post("/admin/flunch/start")
async def start_flunch_automation(bg: BackgroundTasks, admin: str = Depends(get_current_admin)):
    FLUNCH_DIR = os.path.join("script", "flunch")
    
    def run_automation():
        try:
            subprocess.run(["node", "main.js"], cwd=FLUNCH_DIR, check=True)
        except Exception as e:
            print(f"[PY-FLUNCH] ERREUR EXECUTION: {str(e)}")

    bg.add_task(run_automation)
    return {"status": "success", "message": "Orchestrateur lancé en arrière-plan."}
    
# [ ADMIN - PAYMENTS ] =========================================================

@app.get("/admin/payments")
async def get_payments(db: Session = Depends(get_db), admin: str = Depends(get_current_admin)):
    return db.query(Payment).order_by(Payment.created_at.desc()).limit(50).all()

# [ AUTHENTICATION ] ===========================================================

@app.post("/auth/login")
async def login(req: dict = Body(...), db: Session = Depends(get_db)):
    username = req.get("username")
    password = req.get("password")
    admin = db.query(Admin).filter(Admin.username == username).first()
    if not admin or not verify_password(password, admin.hashed_password):
        raise HTTPException(status_code=401, detail="Identifiants invalides")
    
    admin.last_login = datetime.utcnow()
    db.commit()
    
    access_token = create_access_token(data={"sub": admin.username})
    return {"access_token": access_token, "token_type": "bearer"}

# [ ADMIN - STATS ] ============================================================

@app.get("/admin/stats")
async def get_stats(db: Session = Depends(get_db), admin: str = Depends(get_current_admin)):
    total_rev = db.query(func.sum(Payment.amount)).filter(Payment.status == "PAID").scalar() or 0
    paid_count = db.query(Payment).filter(Payment.status == "PAID").count()
    total_count = db.query(Payment).count()
    
    today = datetime.utcnow().date()
    gen_today = db.query(Payment).filter(
        Payment.is_generated == 1,
        Payment.created_at >= today
    ).count()

    return {
        "total_revenue": total_rev,
        "paid_payments": paid_count,
        "total_payments": total_count,
        "generated_today": gen_today
    }

# [ GENERATORS - MRZ/ZIP ] =====================================================

@app.post("/generate-mrz")
async def mrz_endpoint(req: dict = Body(...), admin: str = Depends(get_current_admin)):
    data = generate_random_data()
    if req.get("mode") != "random":
        if req.get("nom"): data["nom"] = req.get("nom")
        if req.get("prenom"): data["prenom"] = req.get("prenom")
    
    mrz_lines = generate_mrz(data)
    return {"mrz": mrz_lines, "data": data}

@app.post("/generate-zip")
async def zip_endpoint(req: dict = Body(...), bg: BackgroundTasks = None, admin: str = Depends(get_current_admin)):
    lines = req.get("lines", [])
    zip_path = generate_qr_zip(lines)
    if bg: bg.add_task(os.remove, zip_path)
    return FileResponse(zip_path, media_type="application/zip", filename="qr_codes.zip")

# [ MAIN - SERVER ] ============================================================

if __name__ == "__main__":
    import uvicorn
    import os
    init_db()
    # On récupère le port de Railway, sinon 8080 par défaut
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
