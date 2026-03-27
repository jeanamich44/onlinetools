import os
import uuid
import zipfile
import shutil
import qrcode
import time
from PIL import Image, ImageDraw, ImageFont
import io

# ==============================================================================

def index_to_letters(index):
    index += 26
    res = ""
    while index > 0:
        index -= 1
        res = chr(65 + (index % 26)) + res
        index //= 26
    return res

# ==============================================================================

def generate_packaging_elite(lines_source: list[str], start_idx: int, title: str = None) -> str:
    uid = str(uuid.uuid4())
    base_tmp = f"temp_pack_{uid}"
    os.makedirs(base_tmp, exist_ok=True)
    
    target_lines = lines_source[start_idx : start_idx + 200]
    if not target_lines:
        raise ValueError("Aucune ligne trouvée.")

    final_zip_path = f"temp_pack_{uid}.zip"
    
    try:
        for i in range(4):
            batch_id = i + 1
            batch_lines = target_lines[i * 50 : (i + 1) * 50]
            if not batch_lines:
                break
            
            txt_filename = f"batch_{batch_id}.txt"
            txt_path = os.path.join(base_tmp, txt_filename)
            with open(txt_path, "w", encoding="utf-8") as bf:
                bf.write("\n".join(batch_lines) + "\n")
            
            qr_tmp_dir = os.path.join(base_tmp, f"qr_tmp_{batch_id}")
            os.makedirs(qr_tmp_dir, exist_ok=True)
            
            for j, line in enumerate(batch_lines, start=1):
                file_id = index_to_letters(j)
                qr_filename = f"{file_id}.png"
                qr_path = os.path.join(qr_tmp_dir, qr_filename)
                
                qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
                qr.add_data(line)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
                
                if title:
                    try:
                        try:
                            fnt = ImageFont.truetype("arial.ttf", 32)
                        except:
                            fnt = ImageFont.load_default()
                            
                        draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))
                        bbox = draw.textbbox((0, 0), title, font=fnt)
                        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
                        
                        max_w = max(img.width, tw) + 40
                        max_h = img.height + th + 60
                        
                        canvas = Image.new("RGB", (max_w, max_h), (255, 0, 0))
                        draw = ImageDraw.Draw(canvas)
                        draw.text(((max_w - tw) // 2, 10), title, font=fnt, fill=(255, 255, 255))
                        canvas.paste(img, ((max_w - img.width) // 2, th + 30))
                        canvas.save(qr_path)
                    except:
                        img.save(qr_path)
                else:
                    img.save(qr_path)
            
            batch_zip_filename = f"batch_{batch_id}.zip"
            batch_zip_path = os.path.join(base_tmp, batch_zip_filename)
            with zipfile.ZipFile(batch_zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
                for file in os.listdir(qr_tmp_dir):
                    z.write(os.path.join(qr_tmp_dir, file), arcname=file)
            
            shutil.rmtree(qr_tmp_dir)

        with zipfile.ZipFile(final_zip_path, 'w', zipfile.ZIP_DEFLATED) as final_z:
            for file in os.listdir(base_tmp):
                final_z.write(os.path.join(base_tmp, file), arcname=file)
                
    finally:
        if os.path.exists(base_tmp):
            shutil.rmtree(base_tmp)
            
    return final_zip_path
