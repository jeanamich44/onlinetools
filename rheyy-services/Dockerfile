# 1. Image de base
FROM python:3.11-slim

# 2. Installation de Node.js
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 3. Dossier de travail
WORKDIR /app

# 4. Copie des fichiers de dépendances
COPY requirements.txt .
COPY package.json .

# 5. Installation des librairies
RUN pip install --no-cache-dir -r requirements.txt
RUN npm install
RUN npx playwright install --with-deps chromium

# 6. Copie de tout le code source
COPY . .

# 7. Lancement via Python (Python gère le Port dynamiquement)
CMD ["python", "main.py"]
