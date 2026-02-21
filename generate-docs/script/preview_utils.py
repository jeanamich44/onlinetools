import fitz

def save_pdf_as_jpg(doc, output_path, zoom=1.8, quality=75):
    """
    Convertit la première page d'un document PDF en image JPG optimisée pour la preview.
    
    Args:
        doc: Objet fitz.Document.
        output_path: Chemin de destination du fichier (doit finir par .jpg).
        zoom: Facteur de zoom pour la résolution (1.8 par défaut).
        quality: Qualité de compression JPG (75 par défaut).
    """
    # Sélection de la première page
    page = doc[0]
    
    # Création du pixmap avec le zoom spécifié
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    
    # Sauvegarde en JPG avec la qualité spécifiée
    pix.save(output_path, jpg_quality=quality)
    
    # Fermeture du document
    doc.close()
