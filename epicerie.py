import streamlit as st
import cv2
import numpy as np
from pyzbar.pyzbar import decode
import requests

st.set_page_config(page_title="Mon Scanner Épicerie", page_icon="🛒", layout="centered")

st.title("🛒 Assistant Épicerie UPC")
st.write("Cliquez sur le bouton ci-dessous pour prendre une photo nette avec l'appareil photo de votre téléphone.")

image_chargee = st.file_uploader("Prendre une photo du code-barres", type=["jpg", "jpeg", "png"])

if image_chargee:
    file_bytes = np.asarray(bytearray(image_chargee.read()), dtype=np.uint8)
    image_cv = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    st.subheader("📸 Photo envoyée :")
    st.image(image_cv, use_container_width=True)
    
    gris = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
    _, gris_ameliore = cv2.threshold(gris, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    st.write("🔍 Analyse en cours...")
    codes_detectes = decode(image_cv)
    if not codes_detectes:
        codes_detectes = decode(gris_ameliore)
        
    if codes_detectes:
        for code in codes_detectes:
            code_upc = code.data.decode('utf-8')
            st.success(f"🎯 Code UPC détecté : {code_upc}")
            
            url = f"https://openfoodfacts.org{code_upc}.json"
            
            entetes = {
                "User-Agent": "MonScannerEpicerie - Android/iOS - Version 1.0 (contact: test@example.com)"
            }
            
            try:
                reponse_brute = requests.get(url, headers=entetes, timeout=10)
                
                if reponse_brute.status_code == 200:
                    reponse = reponse_brute.json()
                    
                    if reponse.get("status") == 1:
                        produit = reponse["product"]
                        
                        # --- CORRECTION DE L'ERREUR DE COLONNES ---
                        # On spécifie '2' pour indiquer qu'on veut couper l'écran en deux colonnes égales
                        col1, col2 = st.columns(2)
                        
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
                else:
                    st.error(f"Le serveur distant a répondu avec une erreur (Code: {reponse_brute.status_code})")
                    
            except Exception as e:
                st.error(f"Erreur de connexion technique : {str(e)}")
            break
    else:
        st.error("❌ Aucun code-barres n'a pu être lu.")
