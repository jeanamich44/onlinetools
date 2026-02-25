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

def flatten_pdf(file_path):
    """
    Rend le PDF non modifiable en convertissant chaque page en image haute résolution
    puis en reconstruisant un PDF à partir de ces images.
    """
    doc = fitz.open(file_path)
    new_doc = fitz.open()

    for page in doc:
        # Conversion en image (zoom 2.0 pour la netteté)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        
        # Nouvelle page aux mêmes dimensions
        new_page = new_doc.new_page(width=page.rect.width, height=page.rect.height)
        
        # On plaque l'image brute (Pixmap)
        new_page.insert_image(page.rect, pixmap=pix)

    doc.close()
    
    # On écrase le fichier original avec la version "plate" sécurisée
    new_doc.save(file_path, garbage=4, deflate=True)
    new_doc.close()
