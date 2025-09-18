import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from PyPDF2 import PdfMerger
import fitz
import io
import os
import re

direction_aliases = {
    "North": ["north", "n"],
    "Northeast": ["northeast", "ne"],
    "East": ["east", "e"],
    "Southeast": ["southeast", "se"],
    "South": ["south", "s"],
    "Southwest": ["southwest", "sw"],
    "West": ["west", "w"],
    "Northwest": ["northwest", "nw"]
}

def normalize_name(name):
    base = os.path.splitext(name)[0]
    return re.sub(r"[\s\-_]+", "", base.lower())

def match_directional_images(files, prefix):
    matched = {}
    used = set()
    for file in files:
        name = file.name.lower()
        norm = normalize_name(file.name)
        if file in used or prefix not in name:
            continue
        for direction, aliases in direction_aliases.items():
            if any(alias in norm for alias in aliases):
                matched[direction] = file
                used.add(file)
                break
    return matched

def extract_template_image(pdf_file):
    data = pdf_file.read()
    doc = fitz.open(stream=data, filetype="pdf")
    page = doc.load_page(1 if doc.page_count > 1 else 0)
    pix = page.get_pixmap(dpi=200)
    return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

def full_page_image(image_file):
    img = Image.open(image_file).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="PDF")
    return buf.getvalue()

def load_font_or_fail(size):
    paths = ["fonts/LiberationSans-Regular.ttf", "LiberationSans-Regular.ttf"]
    for path in paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size=size)
    raise FileNotFoundError("LiberationSans-Regular.ttf not found.")

def create_directional_page(template_img, job_name, title, directional_img):
    canvas = template_img.copy()
    W, H = canvas.size
    draw = ImageDraw.Draw(canvas)
    font = load_font_or_fail(50)

    draw.text((W // 2, int(H * 0.07)), job_name, font=font, anchor="mm", fill="black")
    draw.text((W // 2, int(H * 0.11)), title, font=font, anchor="mm", fill="black")

    directional = Image.open(directional_img).convert("RGB").resize((1600, 1200))
    canvas.paste(directional, (int((W - 1600) / 2), int(H * 0.165)))

    buf = io.BytesIO()
    canvas.save(buf, format="PDF")
    return buf.getvalue()

def generate_report(job_name, launcher_img, receiver_img, directional_imgs, template_pdf):
    template_img = extract_template_image(template_pdf)
    merger = PdfMerger()

    merger.append(io.BytesIO(full_page_image(launcher_img)))
    launcher_matched = match_directional_images(directional_imgs, "launcher")
    for direction in direction_aliases:
        if direction in launcher_matched:
            page = create_directional_page(template_img, job_name, f"Launcher {direction}", launcher_matched[direction])
            merger.append(io.BytesIO(page))

    merger.append(io.BytesIO(full_page_image(receiver_img)))
    receiver_matched = match_directional_images(directional_imgs, "receiver")
    for direction in direction_aliases:
        if direction in receiver_matched:
            page = create_directional_page(template_img, job_name, f"Receiver {direction}", receiver_matched[direction])
            merger.append(io.BytesIO(page))

    buf = io.BytesIO()
    merger.write(buf)
    merger.close()
    return buf

st.set_page_config(page_title="Gibson/Oneok Report Generator", layout="centered")
st.title("📄 Gibson/Oneok Report Generator")

job_name = st.text_input("Enter Job Name")
template_pdf = st.file_uploader("Upload Template PDF", type=["pdf"])
all_images = st.file_uploader("Upload 18 Images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if st.button("Generate Report"):
    if not job_name or not template_pdf or not all_images or len(all_images) != 18:
        st.error("Please upload the template PDF, exactly 18 images, and enter a job name.")
    else:
        launcher_img = next((f for f in all_images if f.name.lower().strip() == "launcher.jpg"), None)
        receiver_img = next((f for f in all_images if f.name.lower().strip() == "receiver.jpg"), None)

        if not launcher_img or not receiver_img:
            st.error("Launcher.jpg and Receiver.jpg must be included.")
        else:
            directional_imgs = [f for f in all_images if f not in [launcher_img, receiver_img]]
            try:
                report = generate_report(job_name, launcher_img, receiver_img, directional_imgs, template_pdf)
                st.success("✅ Report generated successfully!")
                st.download_button("📥 Download Report", data=report, file_name="Final_Report.pdf", mime="application/pdf")
            except Exception as e:
                st.error(f"Error: {e}")
