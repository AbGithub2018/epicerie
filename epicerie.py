import streamlit as st
import cv2
import numpy as np
from pyzbar.pyzbar import decode
import requests

st.set_page_config(page_title="Mon Scanner Épicerie", page_icon="🛒", layout="centered")

st.title("🛒 Assistant Épicerie UPC")
st.write("Prenez une photo bien droite, proche et nette du code-barres.")

image_capturee = st.camera_input("Scanner un produit")

if image_capturee:
    bytes_data = image_capturee.getvalue()
    image_cv = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
    
    # --- AMÉLIORATION DE L'IMAGE POUR ENÉVITER LES ÉCHECS ---
    # 1. Conversion en niveaux de gris (noir et blanc)
    gris = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
    
    # 2. Augmentation du contraste et de la netteté
    # (Aide pyzbar à bien séparer les barres noires des espaces blancs)
    gris_ameliore = cv2.threshold(gris, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    
    # 3. Essayer de décoder sur l'image améliorée, sinon sur l'image originale
    codes_detectes = decode(gris_ameliore)
    if not codes_detectes:
        codes_detectes = decode(image_cv)
    # --------------------------------------------------------
    
    if codes_detectes:
        for code in codes_detectes:
            code_upc = code.data.decode('utf-8')
            st.success(f"🎯 Code UPC détecté : {code_upc}")
            
            url = f"https://openfoodfacts.org{code_upc}.json"
            reponse = requests.get(url).json()
            
            if reponse.get("status") == 1:
                produit = reponse["product"]
                
                col1, col2 = st.columns()
                with col1:
                    url_image = produit.get("image_front_url")
                    if url_image:
                        st.image(url_image, use_container_width=True)
                
                with col2:
                    st.subheader(produit.get("product_name", "Produit inconnu"))
                    st.write(f"**Marque :** {produit.get('brands', 'Inconnue')}")
                    
                    nutriscore = produit.get("nutriscore_grade", "Inconnu").upper()
                    st.write(f"**Score Nutritionnel :** {nutriscore}")
                    
                    allergenes = produit.get("allergens_from_ingredients", "")
                    if allergenes:
                        st.error(f"⚠️ Allergènes : {allergenes}")
            else:
                st.warning("Produit introuvable dans la base de données Nord-Américaine.")
            break
    else:
        st.error("❌ Aucun code-barres détecté.")
        st.info("💡 **Conseil :** Approchez le téléphone pour que le code-barres prenne une bonne partie de l'écran, attendez que l'image soit bien nette (pas de flou de bougé) avant de cliquer.")
