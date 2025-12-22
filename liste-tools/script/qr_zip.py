import os
import uuid
import zipfile
import shutil
import qrcode

MAX_LINES = 4000

def index_to_code(i: int) -> str:
    a = (i // 676) % 26
    b = (i // 26) % 26
    c = i % 26
    return f"{chr(65+a)}{chr(65+b)}{chr(65+c)}"

def generate_qr_zip(lines: list[str]) -> str:
    if not lines:
        raise ValueError("Empty list")

    if len(lines) > MAX_LINES:
        raise ValueError("Too many lines")

    uid = str(uuid.uuid4())
    temp_dir = f"/tmp/{uid}"
    zip_path = f"/tmp/{uid}.zip"

    os.makedirs(temp_dir)

    for i, text in enumerate(lines):
        code = index_to_code(i)
        qr = qrcode.make(text)
        qr.save(f"{temp_dir}/{code}.png")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file in os.listdir(temp_dir):
            zipf.write(os.path.join(temp_dir, file), arcname=file)

    shutil.rmtree(temp_dir)

    return zip_path
