
import streamlit as st
from camera_input_live import camera_input_live
import cv2
import numpy as np
from pyzbar.pyzbar import decode
import requests

# 1. Configuration de l'affichage pour l'écran d'un cellulaire
st.set_page_config(page_title="Mon Scanner Épicerie", page_icon="🛒", layout="centered")

st.title("🛒 Assistant Épicerie UPC")
st.write("Placez le code-barres UPC du produit devant la caméra.")

# 2. Capture du flux vidéo en direct (utilise la caméra arrière du téléphone)
image_capturee = camera_input_live(show_controls=False, key="scanner_upc")

if image_capturee:
    # Convertir l'image capturée pour qu'elle soit lisible par OpenCV
    bytes_data = image_capturee.getvalue()
    image_cv = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
    
    # 3. Décodage du code-barres avec PyZbar
    codes_detectes = decode(image_cv)
    
    if codes_detectes:
        for code in codes_detectes:
            # Vérifier que c'est bien un format UPC (courant aux USA/Canada) ou EAN
            if code.type in ["UPCA", "UPCE", "EAN13"]:
                code_upc = code.data.decode('utf-8')
                
                st.success(f"🎯 Code UPC détecté : {code_upc}")
                
                # 4. Requête vers la base de données alimentaire Nord-Américaine
                url = f"https://openfoodfacts.org{code_upc}.json"
                reponse = requests.get(url).json()
                
                if reponse.get("status") == 1:
                    produit = reponse["product"]
                    
                    # Mise en page des résultats pour le consommateur
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        # Afficher la photo du produit si elle existe
                        url_image = produit.get("image_front_url")
                        if url_image:
                            st.image(url_image, use_container_width=True)
                        else:
                            st.subheader("🖼️")
                    
                    with col2:
                        st.subheader(produit.get("product_name", "Produit inconnu"))
                        st.write(f"**Marque :** {produit.get('brands', 'Inconnue')}")
                        
                        # Affichage du Nutri-Score ou d'autres indices santé
                        nutriscore = produit.get("nutriscore_grade", "Inconnu").upper()
                        st.write(f"**Score Nutritionnel :** {nutriscore}")
                        
                        # Alerte Allergènes (très utile en magasin !)
                        allergenes = produit.get("allergens_from_ingredients", "")
                        if allergenes:
                            st.error(f"⚠️ Allergènes : {allergenes}")
                else:
                    st.warning("Produit introuvable dans la base de données Nord-Américaine.")
                break # On s'arrête au premier code valide détecté à l'écran
    else:
        st.info("🔄 Recherche de code-barres en cours... Alignez le produit.")
