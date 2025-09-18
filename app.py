import streamlit as st
from PyPDF2 import PdfMerger
from PIL import Image
from fpdf import FPDF
import io
import os

# Directional aliases
direction_aliases = {
    "East": ["east", "e", "le", "l east"],
    "Northeast": ["northeast", "ne", "l ne"],
    "North": ["north", "n", "l n"],
    "Northwest": ["northwest", "nw", "l nw"],
    "West": ["west", "w", "l w"],
    "Southwest": ["southwest", "sw", "l sw"],
    "South": ["south", "s", "l s"],
    "Southeast": ["southeast", "se", "l se"]
}

def match_directional_images(files, prefix):
    matched = {}
    for direction, aliases in direction_aliases.items():
        for file in files:
            name = file.name.lower()
            if prefix.lower() in name and any(alias in name for alias in aliases):
                matched[direction] = file
                break
    return matched

def create_image_page(job_name, title, image_file):
    img = Image.open(image_file)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=16)
    pdf.cell(200, 10, txt=job_name, ln=True, align='C')
    pdf.cell(200, 10, txt=title, ln=True, align='C')
    img_path = f"temp_{title.replace(' ', '_')}.jpg"
    img.save(img_path)
    pdf.image(img_path, x=30, y=40, w=150)
    os.remove(img_path)
    return pdf.output(dest='S').encode('latin1')

def generate_report(job_name, launcher_img, receiver_img, launcher_views, receiver_views):
    merger = PdfMerger()

    # Page 1: Launcher.jpg
    launcher_pdf = create_image_page("", "", launcher_img)
    merger.append(io.BytesIO(launcher_pdf))

    # Pages 2–9: Launcher directional images
    launcher_matched = match_directional_images(launcher_views, "launcher")
    for direction in direction_aliases:
        if direction in launcher_matched:
            title = f"Launcher {direction}"
            page = create_image_page(job_name, title, launcher_matched[direction])
            merger.append(io.BytesIO(page))

    # Page 10: Receiver.jpg
    receiver_pdf = create_image_page("", "", receiver_img)
    merger.append(io.BytesIO(receiver_pdf))

    # Pages 11–18: Receiver directional images
    receiver_matched = match_directional_images(receiver_views, "receiver")
    for direction in direction_aliases:
        if direction in receiver_matched:
            title = f"Receiver {direction}"
            page = create_image_page(job_name, title, receiver_matched[direction])
            merger.append(io.BytesIO(page))

    output = io.BytesIO()
    merger.write(output)
    merger.close()
    return output

# Streamlit UI
st.set_page_config(page_title="Gibson/Oneok Report Generator", layout="centered")
st.title("📄 Gibson/Oneok Report Generator")

job_name = st.text_input("Enter Job Name")
all_images = st.file_uploader("Upload All 18 Images (Launcher.jpg, Receiver.jpg, and 16 directional views)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if st.button("Generate Report"):
    if not job_name or len(all_images) != 18:
        st.error("Please upload exactly 18 images and enter a job name.")
    else:
        launcher_img = next((f for f in all_images if f.name.lower() == "launcher.jpg"), None)
        receiver_img = next((f for f in all_images if f.name.lower() == "receiver.jpg"), None)
        directional_imgs = [f for f in all_images if f not in [launcher_img, receiver_img]]

        if not launcher_img or not receiver_img or len(directional_imgs) != 16:
            st.error("Make sure Launcher.jpg and Receiver.jpg are included, plus 16 directional images.")
        else:
            launcher_views = [f for f in directional_imgs if "launcher" in f.name.lower()]
            receiver_views = [f for f in directional_imgs if "receiver" in f.name.lower()]
            report = generate_report(job_name, launcher_img, receiver_img, launcher_views, receiver_views)
            st.success("✅ Report generated successfully!")
            st.download_button("📥 Download Report", data=report, file_name="Final_Report.pdf", mime="application/pdf")
