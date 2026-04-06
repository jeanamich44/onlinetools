# 1. On part d'une image Python officielle
FROM python:3.11-slim

# 2. On installe Node.js et les dépendances système pour Chrome
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 3. On prépare le dossier de travail
WORKDIR /app

# 4. On installe les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. On installe les dépendances Node.js pour l'automate
COPY package.json .
RUN npm install
# On installe aussi les dépendances dans le sous-dossier script/flunch
COPY script/flunch/package.json ./script/flunch/ 2>/dev/null || true
RUN npm install --prefix script/flunch axios playwright node-imap mailparser imap-simple 2>/dev/null || true

# 6. On installe les navigateurs Playwright
RUN npx playwright install --with-deps chromium

# 7. On copie tout le reste du code
COPY . .

# 8. Commande de démarrage
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
