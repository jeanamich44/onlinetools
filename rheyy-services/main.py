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
import asyncio
from fastapi.concurrency import run_in_threadpool
import aiohttp

from systeme.database import init_db, get_db, Payment, Admin, Setting, Revendeur
from systeme.security import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    get_current_admin,
    get_current_revendeur,
    check_ip_whitelist,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from script.mrz import generate_mrz, generate_random_data
from script.qr_zip import generate_qr_zip
from script.packager import generate_packaging_elite
from script.audio_analyse import (
    perform_full_analysis, 
    perform_full_analysis_stream, 
    perform_retry_analysis_stream
)
from systeme.utils import (
    fetch_remote_file_content, 
    get_ssh_client, 
    REMOTE_FILE_CARDS,
    write_remote_file,
    run_remote_bot,
    REMOTE_FILE_DATA,
    REMOTE_FILE_DBFLUNCH,
    REMOTE_BOT_FLUNCH_EXE,
    REMOTE_BOT_FLUNCH_DIR
)
from script.flunch_checker import fetch_flunch_data
from script.chronopost_checker import check_chronopost_stream, dissect_tracking, generate_sequence

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
    form_count = form_data.get("count", "200")
    
    count = min(int(form_count) if str(form_count).strip().isdigit() else 200, 200)
    
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
            
        final_zip = generate_packaging_elite(lines, start_line - 1, title, count)
        setting.value = str(start_line + count)
        db.commit()
        bg.add_task(os.remove, final_zip)
        return FileResponse(final_zip, media_type="application/zip", filename=f"pack_{count}_line_{start_line}.zip")
        
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
        "autorenew":  os.path.join(base_flunch, "logs", "auto_renew_service.log"),
        "mails":      os.path.join(base_flunch, "output", "mails_recus.txt"),
        "token":      os.path.join(base_flunch, "output", "bearer_token.txt")
    }
    
    results = {}
    for key, path in files.items():
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                results[key] = f.read()
        else:
            results[key] = ""
            
    return results

@app.get("/admin/flunch/screenshots")
async def list_flunch_screenshots(admin: str = Depends(get_current_admin)):
    output_dir = os.path.join("script", "flunch", "output")
    if not os.path.exists(output_dir):
        return []
    try:
        files = [f for f in os.listdir(output_dir) if f.startswith("screenshot_") and f.endswith(".png")]
        files.sort(reverse=True)
        return files
    except Exception:
        return []

@app.get("/admin/flunch/screenshot/{filename}")
async def get_specific_screenshot(filename: str, admin: str = Depends(get_current_admin)):
    safe_path = os.path.join("script", "flunch", "output", filename)
    if os.path.exists(safe_path) and ".." not in filename:
        return FileResponse(safe_path, media_type="image/png")
    raise HTTPException(status_code=404, detail="Capture d'écran introuvable")

current_flunch_process = None

@app.post("/admin/flunch/start")
async def start_flunch_automation(bg: BackgroundTasks = None, admin: str = Depends(get_current_admin)):
    global current_flunch_process
    FLUNCH_DIR = os.path.join("script", "flunch")
    
    if current_flunch_process:
        try:
            current_flunch_process.terminate()
        except:
            pass
            
    def run_automation():
        global current_flunch_process
        try:
            current_flunch_process = subprocess.Popen(["node", "main.js"], cwd=FLUNCH_DIR)
            current_flunch_process.wait()
        except Exception as e:
            print(f"[PY-FLUNCH] ERREUR EXECUTION: {str(e)}")
        finally:
            current_flunch_process = None

    if bg:
        bg.add_task(run_automation)
    else:
        run_automation()
        
    return {"status": "success", "message": "Orchestrateur lancé en arrière-plan"}

@app.post("/admin/flunch/stop")
async def stop_flunch_automation(admin: str = Depends(get_current_admin)):
    global current_flunch_process
    
    # Tentative d'arrêt du processus principal
    if current_flunch_process:
        try:
            current_flunch_process.terminate()
            current_flunch_process = None
        except Exception as e:
            print(f"Erreur terminate: {e}")
            
    # Sécurité supplémentaire pour tuer node (utile sur Railway/Linux)
    try:
        if os.name == 'nt':
            os.system("taskkill /F /IM node.exe")
        else:
            os.system("pkill -f 'node main.js'")
        # On va aussi tuer chromium pour être sûr qu'aucun fantôme ne reste
        if os.name == 'nt':
            os.system("taskkill /F /IM chrome.exe")
        else:
            os.system("pkill -f 'chrome'")
    except:
        pass
        
    return {"status": "success", "message": "Le processus et le navigateur ont été arrêtés fermement."}

@app.post("/admin/flunch/check")
async def check_flunch_batch(req: dict = Body(...)):
    ids_raw = req.get("ids", "")
    export_type = req.get("export", "").lower()
    
    if not ids_raw:
        raise HTTPException(status_code=400, detail="Aucun ID fourni")
    
    if isinstance(ids_raw, list):
        id_list = [str(i).strip() for i in ids_raw if str(i).strip()]
    else:
        id_string = str(ids_raw)
        cleaned_ids = id_string.replace("\n", ",").replace("\r", ",")
        id_list = [i.strip() for i in cleaned_ids.split(",") if i.strip()]
    
    async def process_single_id(client_id):
        try:
            data = await run_in_threadpool(fetch_flunch_data, client_id)
            
            if export_type == "bot" and isinstance(data, dict) and "SOLDE" in data:
                try:
                    balance = int(float(data.get("SOLDE", "0")))
                except:
                    balance = 0
                
                card = data.get("CARTE", "N/A")
                
                # Calcul de l'index PX
                px = 0
                if 40 <= balance <= 79: px = 1
                elif 80 <= balance <= 99: px = 2
                elif 100 <= balance <= 149: px = 3
                elif 150 <= balance <= 209: px = 4
                elif 210 <= balance <= 299: px = 5
                elif balance >= 300: px = 6
                
                return f"flunch|{card}:0|{balance}|{px}"
            else:
                return {"id": client_id, "data": data}
        except Exception as e:
            return {"id": client_id, "data": {"status": "error", "message": str(e)}}

    # Exécution en parallèle (limitation possible si besoin, mais ici gather suffit)
    results = await asyncio.gather(*[process_single_id(cid) for cid in id_list])
            
    if export_type == "bot":
        # On ne trie que les chaînes de caractères (les succès formatés)
        bot_lines = [r for r in results if isinstance(r, str)]
        try:
            bot_lines.sort(key=lambda x: int(x.split('|')[2]))
        except:
            pass
        return {"export": "\n".join(bot_lines)}
        
    return {"results": results}

@app.post("/admin/flunch/launch-bot")
async def flunch_launch_bot_endpoint(req: dict = Body(...), admin: str = Depends(get_current_admin)):
    """Reçoit une liste, l'écrit sur le RDP et lance le bot Flunch"""
    results = req.get("results", [])
    if not results:
        raise HTTPException(status_code=400, detail="Aucune donnée à envoyer")
        
    try:
        from systeme.utils import REMOTE_FILE_DATA, REMOTE_BOT_FLUNCH_EXE, REMOTE_BOT_FLUNCH_DIR, write_remote_file, run_remote_bot
        final_content = "\n".join(results)
        # On écrit dans le fichier DATA (data.txt) sur le RDP pour le launcher
        await run_in_threadpool(write_remote_file, REMOTE_FILE_DATA, final_content)
        # On lance l'exécutable Flunch
        await run_in_threadpool(run_remote_bot, REMOTE_BOT_FLUNCH_EXE, REMOTE_BOT_FLUNCH_DIR)
        
        return {"status": "success", "message": "Liste envoyée et Bot Flunch lancé avec succès sur le RDP."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from systeme.utils import fetch_random_lines_remote, REMOTE_FILE_DBFLUNCH
@app.post("/admin/flunch/ssh-random")
async def flunch_ssh_random(req: dict = Body(...), admin: str = Depends(get_current_admin)):
    count = int(req.get("count", 10))
    try:
        lines = await run_in_threadpool(fetch_random_lines_remote, REMOTE_FILE_DBFLUNCH, count)
        return {"lines": lines}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SSH Error: {str(e)}")

@app.get("/generate-flunch-list")
async def public_flunch_generate_list(count: int = 50):
    """
    API publique pour générer une liste de HITS Flunch.
    Extrait des IDs du RDP, les vérifie en temps réel et renvoie les valides.
    """
    if count > 100: count = 100
    try:
        from script.flunch_checker import fetch_flunch_data
        # 1. Extraction d'un échantillon (on prend x2 pour compenser les fails)
        raw_ids = await run_in_threadpool(fetch_random_lines_remote, REMOTE_FILE_DBFLUNCH, count * 2)
        clean_ids = []
        for l in raw_ids:
            if not l.strip(): continue
            parts = l.strip().split('|')
            # Si format flunch|ID:0|... on prend le 2ème segment, sinon le 1er
            token_part = parts[1] if len(parts) > 1 and 'flunch' in parts[0].lower() else parts[0]
            # On garde ce qui est avant le ":" (pour virer le :0)
            clean_ids.append(token_part.split(':')[0].strip())
        
        clean_ids = list(set(clean_ids))
        
        # 2. Check asynchrone en parallèle
        async def check_id(card_id):
            try:
                res = await fetch_flunch_data(card_id)
                if res and res.get('status') == 'HIT':
                    return f"flunch|{card_id}:0|{res['solde']}|{res['points']}"
            except: pass
            return None

        tasks = [check_id(cid) for cid in clean_ids[:count*2]]
        checked_results = await asyncio.gather(*tasks)
        
        # 3. Filtrage des hits et limitation au nombre demandé
        hits = [r for r in checked_results if r][:count]
        
        return StreamingResponse(iter(["\n".join(hits)]), media_type="text/plain")
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})

# [ CHRONOPOST ] ===============================================================

@app.post("/analyze-chronopost-stream")
async def analyze_chronopost_streaming_endpoint(request: Request, admin: str = Depends(get_current_admin)):
    form_data = await request.form()
    mode = form_data.get("mode", "check")
    keyword = form_data.get("keyword")
    source = form_data.get("source", "file")
    
    targets = []
    
    if source == "file":
        file = form_data.get("file")
        if not file:
            raise HTTPException(status_code=400, detail="Fichier manquant")
        content = await file.read()
        targets = [l.strip() for l in content.decode("utf-8", errors="ignore").splitlines() if l.strip()]
    else:
        base = str(form_data.get("base", "")).replace(" ", "")
        start_index = form_data.get("start_index")
        count = int(form_data.get("count", 10))
        
        prefix, digits, suffix = dissect_tracking(base)
        if not prefix:
            raise HTTPException(status_code=400, detail="Format de base invalide")
        
        if not start_index:
            start_index = digits
            
        targets = generate_sequence(prefix, digits, suffix, start_index, count)
        
    if not targets:
        raise HTTPException(status_code=400, detail="Aucune cible à analyser")

    async def event_generator():
        for res_json in check_chronopost_stream(targets, mode, keyword):
            yield res_json

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")

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

# [ ENDPOINTS SERVICES ] =======================================================

@app.get("/admin/settings")
async def get_all_settings(db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    settings = db.query(Setting).all()
    return {s.key: s.value for s in settings}

@app.post("/admin/settings")
async def update_settings(data: dict = Body(...), db: Session = Depends(get_db), admin: Admin = Depends(get_current_admin)):
    for key, value in data.items():
        setting = db.query(Setting).filter(Setting.key == key).first()
        if setting:
            setting.value = str(value)
        else:
            new_s = Setting(key=key, value=str(value))
            db.add(new_s)
    db.commit()
    return {"status": "success"}

@app.get("/public/settings")
async def get_public_settings(db: Session = Depends(get_db)):
    # On renvoie uniquement ce qui est utile au client/Revendeur
    keys = ["site_name", "tg_support", "min_recharge", "max_recharge", "recharge_Revendeur_enabled"]
    settings = db.query(Setting).filter(Setting.key.in_(keys)).all()
    return {s.key: s.value for s in settings}

@app.get("/service/cards")
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
        for key in ["nom", "prenom", "dep", "canton", "bureau", "date_delivrance", "random_code", "naissance", "sexe"]:
            if req.get(key):
                data[key] = req.get(key)
    
    mrz_lines = generate_mrz(data)
    return {"mrz": mrz_lines, "data": data}

@app.post("/generate-zip")
async def zip_endpoint(req: dict = Body(...), bg: BackgroundTasks = None, admin: str = Depends(get_current_admin)):
    lines = req.get("lines", [])
    zip_path = generate_qr_zip(lines)
    if bg: bg.add_task(os.remove, zip_path)
    return FileResponse(zip_path, media_type="application/zip", filename="qr_codes.zip")

# [ Revendeur ] =================================================================

@app.post("/revendeur/login")
async def Revendeur_login(req: dict = Body(...), db: Session = Depends(get_db)):
    username = req.get("username", "").strip()
    password = req.get("password", "")
    
    if not username or not password:
        return JSONResponse(status_code=403, content={})
    
    revendeur = db.query(Revendeur).filter(Revendeur.username == username).first()
    
    if not Revendeur or not verify_password(password, Revendeur.hashed_password):
        return JSONResponse(status_code=403, content={})
    
    if not Revendeur.is_active:
        return JSONResponse(status_code=403, content={})
    
    Revendeur.last_login = datetime.utcnow()
    Revendeur.total_requests += 1
    db.commit()
    
    token = create_access_token(
        data={"sub": Revendeur.username, "role": "revendeur"},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {
        "status": "success",
        "token": token,
        "username": Revendeur.username,
        "balance": Revendeur.balance,
        "categories": Revendeur.categories,
        "role": Revendeur.role
    }

@app.post("/admin/revendeurs")
async def create_revendeur(req: dict = Body(...), db: Session = Depends(get_db), admin: str = Depends(get_current_admin)):
    username = req.get("username", "").strip()
    password = req.get("password", "")
    role = req.get("role", "standard")
    categories = req.get("categories", "")
    balance = float(req.get("balance", 0))
    note = req.get("note", "")
    
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username et password requis")
    
    if len(password) < 4:
        raise HTTPException(status_code=400, detail="Password trop court (min 4)")
    
    existing = db.query(Revendeur).filter(Revendeur.username == username).first()
    if existing:
        raise HTTPException(status_code=409, detail="Ce username existe déjà")
    
    revendeur = Revendeur(
        username=username,
        hashed_password=get_password_hash(password),
        role=role,
        categories=categories,
        balance=balance,
        note=note
    )
    db.add(revendeur)
    db.commit()
    db.refresh(revendeur)
    
    return {
        "status": "success",
        "revendeur": {
            "id": revendeur.id,
            "username": revendeur.username,
            "role": revendeur.role,
            "balance": revendeur.balance,
            "categories": revendeur.categories,
            "is_active": revendeur.is_active,
            "created_at": str(revendeur.created_at)
        }
    }

@app.get("/admin/revendeurs")
async def list_revendeurs(db: Session = Depends(get_db), admin: str = Depends(get_current_admin)):
    revendeurs = db.query(Revendeur).order_by(Revendeur.created_at.desc()).all()
    return [{
        "id": r.id,
        "username": r.username,
        "role": r.role,
        "balance": r.balance,
        "categories": r.categories,
        "is_active": r.is_active,
        "total_purchases": r.total_purchases,
        "total_payment_requests": r.total_payment_requests,
        "total_requests": r.total_requests,
        "note": r.note,
        "created_at": str(r.created_at),
        "last_login": str(r.last_login) if r.last_login else None
    } for r in Revendeurs]

@app.get("/admin/transactions")
async def list_all_transactions(db: Session = Depends(get_db), admin: str = Depends(get_current_admin)):
    transactions = db.query(Transaction).order_by(Transaction.date.desc()).all()
    res = []
    for t in transactions:
        revendeur = db.query(Revendeur).filter(Revendeur.id == t.Revendeur_id).first()
        res.append({
            "id": t.id,
            "revendeur_username": Revendeur.username if Revendeur else "Inconnu",
            "amount": t.amount,
            "type": t.type,
            "date": str(t.date),
            "status": t.status
        })
    return res

# [ ENDPOINTS RevendeurS ] ======================================================

@app.get("/revendeur/history")
async def get_Revendeur_history(db: Session = Depends(get_db), current_revendeur: Revendeur = Depends(get_current_revendeur)):
    payments = db.query(Payment).filter(
        Payment.user_data == current_revendeur.username, 
        Payment.status == "PAID"
    ).order_by(Payment.created_at.desc()).all()
    return payments


class RechargeInitRequest(BaseModel):
    amount: float

@app.post("/revendeur/create-checkout")
async def create_checkout_Revendeur(req: RechargeInitRequest, db: Session = Depends(get_db), current_revendeur: Revendeur = Depends(get_current_revendeur)):
    # Récupération des réglages
    settings = {s.key: s.value for s in db.query(Setting).all()}
    
    # Vérification si activé
    if settings.get("recharge_Revendeur_enabled") == "false":
        raise HTTPException(status_code=403, detail="Le rechargement par SumUp est temporairement désactivé.")
        
    # Vérification des limites
    min_r = float(settings.get("min_recharge", 1))
    max_r = float(settings.get("max_recharge", 70))
    
    if req.amount < min_r or req.amount > max_r:
        raise HTTPException(status_code=400, detail=f"Montant invalide. Le montant doit être compris entre {min_r}€ et {max_r}€.")

    API_DOCS_URL = "https://generate-docs-production.up.railway.app/api/services/create-recharge"
    
    async with aiohttp.ClientSession() as session:
        async with session.post(API_DOCS_URL, json={"amount": req.amount, "user_id": current_revendeur.username}) as resp:
            if resp.status != 200:
                raise HTTPException(status_code=500, detail="Erreur création checkout")
            data = await resp.json()
            # On log aussi l'intention de paiement en local (PENDING)
            new_p = Payment(
                checkout_id=data["checkout_id"],
                checkout_ref=data["checkout_ref"],
                amount=req.amount,
                status="PENDING",
                user_data=current_revendeur.username,
                product_name="recharge"
            )
            db.add(new_p)
            db.commit()
            return {"status": "success", "checkout_id": data["checkout_id"], "checkout_ref": data["checkout_ref"], "checkout_url": data["url"]}

class RechargeVerifyRequest(BaseModel):
    checkout_ref: str

@app.post("/revendeur/verify-recharge")
async def verify_recharge_Revendeur(req: RechargeVerifyRequest, db: Session = Depends(get_db), current_revendeur: Revendeur = Depends(get_current_revendeur)):
    # 1. Vérifier si on a déjà validé ce paiement en local
    local_payment = db.query(Payment).filter(Payment.checkout_ref == req.checkout_ref).first()
    
    if local_payment and local_payment.status == "PAID":
        return {"status": "success", "new_balance": current_revendeur.balance, "message": "Déjà crédité"}

    API_DOCS_URL = f"https://generate-docs-production.up.railway.app/api/services/verify-recharge/{req.checkout_ref}"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(API_DOCS_URL) as resp:
            if resp.status != 200:
                raise HTTPException(status_code=404, detail="Paiement introuvable")
            data = await resp.json()
            
            if data["status"] == "PAID":
                amount = float(data["amount"])
                
                # Mise à jour du solde
                current_revendeur.balance += amount
                db.add(current_revendeur)
                
                # Mise à jour ou création du paiement local en "PAID"
                if local_payment:
                    local_payment.status = "PAID"
                else:
                    local_payment = Payment(
                        checkout_ref=req.checkout_ref,
                        amount=amount,
                        status="PAID",
                        user_data=current_revendeur.username,
                        product_name="recharge"
                    )
                    db.add(local_payment)
                
                db.commit()
                return {"status": "success", "new_balance": current_revendeur.balance, "message": "Compte crédité"}
            else:
                return {"status": "pending", "payment_status": data["status"]}


# [ MAIN - SERVER ] ============================================================

if __name__ == "__main__":
    import uvicorn
    import os
    import subprocess
    
    init_db()
    
    # Lancement du service Auto-Renew au démarrage
    try:
        auto_renew_path = os.path.join("script", "flunch")
        subprocess.Popen(["node", "auto_renew.js"], cwd=auto_renew_path)
        print("[SYSTEM] Service Auto-Renew lancé avec succès.")
    except Exception as e:
        print(f"[ERROR] Impossible de lancer le service Auto-Renew: {e}")

    # On récupère le port de Railway, sinon 8080 par défaut
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
