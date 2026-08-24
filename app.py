import streamlit as st
import pytesseract
import cv2
import numpy as np
import re
from PIL import Image

st.set_page_config(page_title="Catering Report Calculator", layout="centered")

st.title("📋 Catering Sheet Calculator")
st.write("Upload a sheet image or take a photo to compute totals automatically.")

HOT_MEAL_CODES = {"BUTERC", "VBY", "CBY", "CHANA", "JAINVG", "RAJMA", "CPASTA", "CPOP"}
HOT_MEAL_KEYWORDS = ["RICE", "BIRYANI", "CURRY", "MASALA", "PARATHA", "PASTA", "MAC AND CHEESE"]

def process_image(pil_img):
    img = np.array(pil_img)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Preprocessing to sharpen text
    gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    
    # Extract text with layout structure
    text = pytesseract.image_to_string(gray, config="--psm 6")
    lines = text.splitlines()

    total_qty = 0
    total_hot_cutlery = 0
    total_hot_plates = 0
    total_biryani_yoghurt = 0
    total_coffee = 0
    
    for line in lines:
        upper = line.upper()
        
        # Check if line contains a catering entry
        if "T3L" in upper or any(code in upper for code in HOT_MEAL_CODES):
            qty_match = re.findall(r'\b\d+\b', line)
            if not qty_match:
                continue
            
            qty = int(qty_match[-1])
            
            # Identify Hot Meals
            is_hot = any(code in upper for code in HOT_MEAL_CODES) or \
                     (any(k in upper for k in HOT_MEAL_KEYWORDS) and not any(sw in upper for sw in ["SANDWICH", "SW", "CROISSANT"]))
            
            total_qty += qty
            
            if is_hot:
                total_hot_cutlery += qty
                total_hot_plates += qty
                
            if "VBY" in upper or "CBY" in upper or "BIRYANI" in upper:
                total_biryani_yoghurt += qty
                
            if "COFFEE" in upper:
                total_coffee += qty

    return {
        "Total Count (All Items)": total_qty,
        "Cutlery (Hot Meals Only)": total_hot_cutlery,
        "Paper Tray / Plates (Hot Meals Only)": total_hot_plates,
        "Yoghurt (VBY & CBY Only)": total_biryani_yoghurt,
        "Coffee": total_coffee
    }

# File Upload / Camera Input
uploaded_file = st.file_uploader("Choose an image or take a photo...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Sheet", use_container_width=True)
    
    with st.spinner("Processing image and calculating..."):
        results = process_image(image)
    
    st.success("Calculation Complete!")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Items", results["Total Count (All Items)"])
        st.metric("Cutlery (Hot Meals)", results["Cutlery (Hot Meals Only)"])
        st.metric("Coffee", results["Coffee"])
    with col2:
        st.metric("Paper Trays (Hot Meals)", results["Paper Tray / Plates (Hot Meals Only)"])
        st.metric("Yoghurt (Biryani)", results["Yoghurt (VBY & CBY Only)"])
