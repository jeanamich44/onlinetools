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
from script.audio_analyse import perform_full_analysis, perform_full_analysis_stream, perform_retry_analysis_stream
import shutil
import os

# ==============================================================================

app = FastAPI(title="Rheyy Services", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

audio_files = {}

# ==============================================================================

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
    
    if form_start and int(form_start) > 0:
        start_line = int(form_start)
    else:
        start_line = int(setting.value)
    
    lines = []
    if source == "remote":
        from script.ssh_utils import fetch_remote_file_content, REMOTE_FILE_CARDS
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
        
    try:
        final_zip = generate_packaging_elite(lines, start_line - 1, title)
        setting.value = str(start_line + 200)
        db.commit()
        bg.add_task(os.remove, final_zip)
        return FileResponse(final_zip, media_type="application/zip", filename=f"pack_200_line_{start_line}.zip")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

from script.ssh_utils import fetch_remote_file_content, REMOTE_FILE_CARDS

@app.get("/tools/fetch-remote-cards")
async def fetch_remote_cards_endpoint(admin: str = Depends(get_current_admin)):
    try:
        # On vérifie juste si on peut accéder au fichier sans renvoyer tout le contenu (10000 lignes)
        from script.ssh_utils import get_ssh_client, REMOTE_FILE_CARDS
        ssh = get_ssh_client()
        sftp = ssh.open_sftp()
        stat = sftp.stat(REMOTE_FILE_CARDS)
        sftp.close()
        ssh.close()
        return {"status": "available", "size": stat.st_size}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SSH Check Error: {str(e)}")

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

@app.post("/analyze-audio-confirm")
async def analyze_audio_confirm_endpoint(req: dict = Body(...), admin: str = Depends(get_current_admin)):
    file_id = req.get("file_id")
    numbers = req.get("numbers", [])
    temp_path = audio_files.pop(file_id, None)
    
    if numbers:
        from script.audio_analyse import send_to_remote_ssh
        send_to_remote_ssh(numbers)
        
    if temp_path and os.path.exists(temp_path):
        os.remove(temp_path)
        
    return {"status": "success", "message": "Nombres envoyés avec succès."}

# ==============================================================================

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

@app.get("/admin/payments")
async def get_payments(db: Session = Depends(get_db), admin: str = Depends(get_current_admin)):
    return db.query(Payment).order_by(Payment.created_at.desc()).limit(50).all()

# ==============================================================================

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

# ==============================================================================

if __name__ == "__main__":
    import uvicorn
    init_db()
    uvicorn.run(app, host="0.0.0.0", port=8080)
