from urllib.parse import quote_plus
from fastapi import HTTPException

FRONT_DOMAIN = "https://chezrheyy.ink"

CHRONO_PAGE_MAP = {
    "chrono13": "chrono13.html",
    "chrono10": "chrono10.html",
    "chrono-relais13": "chrono-relais13.html",
    "chrono-relais-europe": "chrono-relais-europe.html",
    "chrono-express": "chrono-express.html"
}

# ==============================================================================
# REDIRECTIONS
# ==============================================================================

def chrono_redirect_url(type_pdf, email):
    target_page = CHRONO_PAGE_MAP.get(type_pdf, "chrono13.html")
    return f"{FRONT_DOMAIN}/chronopost/{target_page}?success_mail={quote_plus(email)}"

# ==============================================================================
# PAGES HTML
# ==============================================================================

# Les pages de succès HTML ont été supprimées au profit des Pop-up dynamiques.
def waiting_spinner_page():
    return """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
      <meta charset="UTF-8">
      <meta http-equiv="refresh" content="5">
      <title>Validation du paiement...</title>
      <style>
        body { font-family: sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; margin: 0; background: #f8f9fa; }
        .spinner { width: 60px; height: 60px; border: 6px solid #e9ecef; border-top: 6px solid #3498db; border-radius: 50%; animation: spin 1s linear infinite; margin-bottom: 30px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .text { font-size: 1.2rem; color: #495057; text-align: center; }
        .subtext { margin-top: 10px; font-size: 0.9rem; color: #6c757d; }
      </style>
    </head>
    <body>
      <div class="spinner"></div>
      <div class="text">Validation de votre paiement par SumUp...</div>
      <div class="subtext">Le téléchargement débutera automatiquement dès la confirmation.<br>N'actualisez pas manuellement la page.</div>
    </body>
    </html>
    """

def payment_not_found_page():
    return "<h1>Paiement non trouvé</h1><p>Veuillez contacter le support.</p>"

def error_page(message):
    return f"<h1>Erreur Système</h1><p>{message}</p>"

# ==============================================================================
# HTTP EXCEPTIONS
# ==============================================================================

def raise_400():
    raise HTTPException(status_code=400, detail="error")

def raise_402():
    raise HTTPException(status_code=402, detail="error")

def raise_404():
    raise HTTPException(status_code=404, detail="error")

def raise_429():
    raise HTTPException(status_code=429, detail="error")

def raise_500():
    raise HTTPException(status_code=500, detail="error")
