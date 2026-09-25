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
    # 1. Charger l'image prise par le cellulaire
    bytes_data = image_capturee.getvalue()
    image_cv = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
    
    # 2. Afficher la photo à l'écran pour vérification de l'utilisateur
    st.subheader("📸 Votre photo reçue par le système :")
    st.image(image_cv, caption="Vérifiez si les lignes du code-barres sont parfaitement nettes et lisibles ici.", use_container_width=True)
    
    # 3. Traitement de l'image (Correction du bogue de tuple OpenCV)
    gris = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
    _, gris_ameliore = cv2.threshold(gris, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # 4. Tentative de décodage
    st.write("🔍 Analyse du code-barres en cours...")
    codes_detectes = decode(gris_ameliore)
    if not codes_detectes:
        codes_detectes = decode(image_cv)
    
    # 5. Résultat du scan
    if codes_detectes:
        for code in codes_detectes:
            code_upc = code.data.decode('utf-8')
            st.success(f"🎯 Code UPC détecté : {code_upc}")
            
            # Appel API Open Food Facts
            url = f"https://openfoodfacts.org{code_upc}.json"
            try:
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
            except Exception as e:
                st.error("Erreur de connexion à la base de données.")
            break
    else:
        st.error("❌ Aucun code-barres n'a pu être lu sur cette photo.")
        st.info("💡 **Comment savoir si votre photo est correcte ?** Regardez l'image affichée ci-dessus. Si vous n'arrivez pas à distinguer clairement chaque petite ligne noire à l'œil nu à cause du flou, de la distance ou d'un reflet brillant, l'algorithme Python ne le pourra pas non plus.")
