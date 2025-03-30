import streamlit as st
import cv2
import numpy as np
from PIL import Image
import requests
import json
import io
import base64
from fpdf import FPDF
import tempfile
from pdf2image import convert_from_bytes
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(
    page_title="Math Problem Solver",
    page_icon="🧮",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
.scan-animation {
    border: 2px solid #2196F3;
    position: relative;
    overflow: hidden;
}
.scan-animation::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 20px;
    background: linear-gradient(transparent, #2196F3, transparent);
    animation: scan 1.5s linear infinite;
}
@keyframes scan {
    0% { top: 0; }
    100% { top: 100%; }
}
</style>
""", unsafe_allow_html=True)

class MathSolver:
    def __init__(self):
        self.OPENROUTER_API_KEY = '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'
        self.API_URL = "https://openrouter.ai/api/v1/chat/completions"
        
    def get_solution(self, problem):
        headers = {
            "Authorization": f"Bearer {self.OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        prompt = f"""Analyze and solve this math/physics/statistics problem step by step:
        
Problem: {problem}

Please provide:
1. Problem statement
2. Step-by-step solution using LaTeX for mathematical expressions
3. Explanation for each step
4. Final answer with verification
5. Note any assumptions made

Use LaTeX for all mathematical expressions and equations."""

        data = {
            "model": "deepseek/deepseek-v3-base:free",
            "messages": [{"role": "user", "content": prompt}]
        }
        
        try:
            response = requests.post(self.API_URL, headers=headers, json=data)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            return f"Error getting solution: {str(e)}"

def process_image(image):
    # Convert to grayscale and apply OCR preprocessing
    img_array = np.array(image)
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    return Image.fromarray(thresh)

def create_pdf(content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=content)
    return pdf.output(dest='S').encode('latin-1')

def main():
    st.title("🧮 Math Problem Solver")
    st.subheader("Upload your math problem and get step-by-step solutions")
    
    solver = MathSolver()
    
    # Input methods
    input_method = st.radio(
        "Choose input method:",
        ["Text Input", "Camera", "Image Upload", "PDF Upload"]
    )
    
    problem_text = None
    
    if input_method == "Text Input":
        problem_text = st.text_area("Enter your math problem:", height=100)
        
    elif input_method == "Camera":
        camera_col, preview_col = st.columns(2)
        with camera_col:
            camera_input = st.camera_input("Take a picture of your problem")
            if camera_input:
                st.markdown('<div class="scan-animation">', unsafe_allow_html=True)
                processed_image = process_image(Image.open(camera_input))
                st.image(processed_image, caption="Processed Image")
                st.markdown('</div>', unsafe_allow_html=True)
                # Here you would add OCR processing
                problem_text = "Please type the problem text for now (OCR integration coming soon)"
                
    elif input_method == "Image Upload":
        uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            st.markdown('<div class="scan-animation">', unsafe_allow_html=True)
            image = Image.open(uploaded_file)
            processed_image = process_image(image)
            st.image(processed_image, caption="Processed Image")
            st.markdown('</div>', unsafe_allow_html=True)
            # Here you would add OCR processing
            problem_text = "Please type the problem text for now (OCR integration coming soon)"
            
    elif input_method == "PDF Upload":
        uploaded_pdf = st.file_uploader("Upload a PDF", type=["pdf"])
        if uploaded_pdf:
            st.markdown('<div class="scan-animation">', unsafe_allow_html=True)
            pdf_bytes = uploaded_pdf.read()
            images = convert_from_bytes(pdf_bytes)
            for i, image in enumerate(images):
                st.image(image, caption=f"Page {i+1}")
            st.markdown('</div>', unsafe_allow_html=True)
            # Here you would add OCR processing
            problem_text = "Please type the problem text for now (OCR integration coming soon)"
    
    if problem_text:
        if st.button("Solve Problem"):
            with st.spinner("Solving your problem..."):
                solution = solver.get_solution(problem_text)
                
                # Display solution
                st.markdown("## Solution")
                st.markdown(solution)
                
                # Export options
                st.markdown("## Export Options")
                col1, col2 = st.columns(2)
                
                with col1:
                    # Copy to clipboard button
                    st.markdown(f"""
                    <textarea id="solution" style="position: absolute; left: -9999px;">{solution}</textarea>
                    <button onclick="
                        var copyText = document.getElementById('solution');
                        copyText.select();
                        document.execCommand('copy');
                    ">Copy Solution</button>
                    """, unsafe_allow_html=True)
                
                with col2:
                    # Download PDF
                    pdf = create_pdf(solution)
                    st.download_button(
                        label="Download PDF",
                        data=pdf,
                        file_name="solution.pdf",
                        mime="application/pdf"
                    )

if __name__ == "__main__":
    main()