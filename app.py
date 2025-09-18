import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from PyPDF2 import PdfMerger
import fitz  # PyMuPDF
import io

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
    used_files = set()
    for direction, aliases in direction_aliases.items():
        for file in files:
            name = file.name.lower()
            if file in used_files:
                continue
            if prefix.lower() in name and any(alias in name for alias in aliases):
                matched[direction] = file
                used_files.add(file)
                break
    return matched

def extract_template_image(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    page_index = 1 if doc.page_count > 1 else 0
    page = doc.load_page(page_index)
    pix = page.get_pixmap(dpi=200)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    return img

def full_page_image(image_file):
    img = Image.open(image_file).convert("RGB")
    output = io.BytesIO()
    img.save(output, format="PDF")
    return output.getvalue()

def create_directional_page(template_img, job_name, title, directional_img):
    canvas = template_img.copy()
    W, H = canvas.size
    draw = ImageDraw.Draw(canvas)

    try:
        font = ImageFont.truetype("arial.ttf", size=144)
    except:
        font = ImageFont.load_default()

    draw.text((W // 2, int(H * 0.15)), job_name, font=font, anchor="mm", fill="black")
    draw.text((W // 2, int(H * 0.25)), title, font=font, anchor="mm", fill="black")

    directional = Image.open(directional_img).convert("RGB")
    directional = directional.resize((int(W * 0.8), int(H * 0.6)))
    canvas.paste(directional, (int(W * 0.1), int(H * 0.35)))

    output = io.BytesIO()
    canvas.save(output, format="PDF")
    return output.getvalue()

def generate_report(job_name, launcher_img, receiver_img, launcher_views, receiver_views, template_pdf):
    template_img = extract_template_image(template_pdf)
    merger = PdfMerger()

    merger.append(io.BytesIO(full_page_image(launcher_img)))

    launcher_matched = match_directional_images(launcher_views, "launcher")
    for direction in direction_aliases:
        if direction in launcher_matched:
            title = f"Launcher {direction}"
            page = create_directional_page(template_img, job_name, title, launcher_matched[direction])
            merger.append(io.BytesIO(page))

    merger.append(io.BytesIO(full_page_image(receiver_img)))

    receiver_matched = match_directional_images(receiver_views, "receiver")
    for direction in direction_aliases:
        if direction in receiver_matched:
            title = f"Receiver {direction}"
            page = create_directional_page(template_img, job_name, title, receiver_matched[direction])
            merger.append(io.BytesIO(page))

    output = io.BytesIO()
    merger.write(output)
    merger.close()
    return output

st.set_page_config(page_title="Gibson/Oneok Report Generator", layout="centered")
st.title("📄 Gibson/Oneok Report Generator")

job_name = st.text_input("Enter Job Name")
template_pdf = st.file_uploader("Upload Template PDF (with branding)", type=["pdf"])
all_images = st.file_uploader("Upload All 18 Images (Launcher.jpg, Receiver.jpg, and 16 directional views)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if st.button("Generate Report"):
    if not job_name or not template_pdf or len(all_images) != 18:
        st.error("Please upload the template PDF, exactly 18 images, and enter a job name.")
    else:
        launcher_img = next((f for f in all_images if f.name.lower() == "launcher.jpg"), None)
        receiver_img = next((f for f in all_images if f.name.lower() == "receiver.jpg"), None)
        directional_imgs = [f for f in all_images if f not in [launcher_img, receiver_img]]

        if not launcher_img or not receiver_img or len(directional_imgs) != 16:
            st.error("Make sure Launcher.jpg and Receiver.jpg are included, plus 16 directional images.")
        else:
            launcher_views = [f for f in directional_imgs if "launcher" in f.name.lower()]
            receiver_views = [f for f in directional_imgs if "receiver" in f.name.lower()]
            report = generate_report(job_name, launcher_img, receiver_img, launcher_views, receiver_views, template_pdf)
            st.success("✅ Report generated successfully!")
            st.download_button("📥 Download Report", data=report, file_name="Final_Report.pdf", mime="application/pdf")
