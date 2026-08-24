import streamlit as st
import easyocr
import cv2
import numpy as np
import re
from PIL import Image

st.set_page_config(page_title="Catering Report Calculator", layout="centered")

st.title("📋 Catering Sheet Calculator")
st.write("Upload a sheet image or take a photo to compute totals automatically.")

@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'], gpu=False)

reader = load_ocr()

HOT_MEAL_CODES = {"BUTERC", "VBY", "CBY", "CHANA", "JAINVG", "RAJMA", "CPASTA", "CPOP"}
HOT_MEAL_KEYWORDS = ["RICE", "BIRYANI", "CURRY", "MASALA", "PARATHA", "PASTA", "MAC AND CHEESE"]

def process_image(pil_img):
    img = np.array(pil_img)
    results = reader.readtext(img)
    
    # Sort boxes top to bottom
    sorted_boxes = sorted(results, key=lambda x: x[0][0][1])
    
    lines = []
    current_line = []
    current_y = -1
    threshold = 15
    
    for bbox, text, _ in sorted_boxes:
        y_center = (bbox[0][1] + bbox[2][1]) / 2
        if current_y == -1 or abs(y_center - current_y) < threshold:
            current_line.append((bbox[0][0], text))
            current_y = y_center
        else:
            current_line.sort(key=lambda x: x[0])
            lines.append(" | ".join([t[1] for t in current_line]))
            current_line = [(bbox[0][0], text)]
            current_y = y_center
            
    if current_line:
        current_line.sort(key=lambda x: x[0])
        lines.append(" | ".join([t[1] for t in current_line]))

    total_qty = 0
    total_hot_cutlery = 0
    total_hot_plates = 0
    total_biryani_yoghurt = 0
    total_coffee = 0
    
    for line in lines:
        upper = line.upper()
        if "T3L" in upper:
            qty_match = re.findall(r'\b\d+\b', line)
            if not qty_match:
                continue
            
            qty = int(qty_match[-1])
            
            # Check if Hot Meal
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
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Sheet", use_container_width=True)
    
    with st.spinner("Processing image and calculating..."):
        results = process_image(image)
    
    st.success("Calculation Complete!")
    
    # Display Results in clean metric cards
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Items", results["Total Count (All Items)"])
        st.metric("Cutlery (Hot Meals)", results["Cutlery (Hot Meals Only)"])
        st.metric("Coffee", results["Coffee"])
    with col2:
        st.metric("Paper Trays (Hot Meals)", results["Paper Tray / Plates (Hot Meals Only)"])
        st.metric("Yoghurt (Biryani)", results["Yoghurt (VBY & CBY Only)"])

