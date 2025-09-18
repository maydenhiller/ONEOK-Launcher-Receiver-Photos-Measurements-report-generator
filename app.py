import streamlit as st
from PyPDF2 import PdfMerger
from PIL import Image
from fpdf import FPDF
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

def match_images(files, prefix):
    matched = {}
    for direction, aliases in direction_aliases.items():
        for file in files:
            name = file.name.lower()
            if any(f"{prefix.lower()} {alias}" in name for alias in aliases):
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
    img_path = f"temp_{title}.jpg"
    img.save(img_path)
    pdf.image(img_path, x=30, y=40, w=150)
    return pdf.output(dest='S').encode('latin1')

def generate_report(job_name, launcher_pdf, receiver_pdf, launcher_imgs, receiver_imgs):
    merger = PdfMerger()

    # Page 1: Launcher.jpg
    merger.append(launcher_pdf)

    # Pages 2–9: Launcher directional images
    launcher_matched = match_images(launcher_imgs, "launcher")
    for direction in direction_aliases:
        if direction in launcher_matched:
            title = f"Launcher {direction}"
            page = create_image_page(job_name, title, launcher_matched[direction])
            merger.append(io.BytesIO(page))

    # Page 10: Receiver.pdf
    merger.append(receiver_pdf)

    # Pages 11–18: Receiver directional images
    receiver_matched = match_images(receiver_imgs, "receiver")
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
st.title("Gibson/Oneok Report Generator")

job_name = st.text_input("Enter Job Name")
launcher_pdf = st.file_uploader("Upload Launcher.jpg (as PDF)", type=["pdf"])
receiver_pdf = st.file_uploader("Upload Receiver.pdf", type=["pdf"])
all_images = st.file_uploader("Upload 16 Directional Images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if st.button("Generate Report"):
    if not job_name or not launcher_pdf or not receiver_pdf or len(all_images) != 16:
        st.error("Please provide job name, both PDFs, and exactly 16 images.")
    else:
        launcher_imgs = [f for f in all_images if "launcher" in f.name.lower()]
        receiver_imgs = [f for f in all_images if "receiver" in f.name.lower()]
        if len(launcher_imgs) != 8 or len(receiver_imgs) != 8:
            st.error("Make sure you have 8 Launcher and 8 Receiver images.")
        else:
            report = generate_report(job_name, launcher_pdf, receiver_pdf, launcher_imgs, receiver_imgs)
            st.success("Report generated successfully!")
            st.download_button("Download Report", data=report, file_name="Final_Report.pdf", mime="application/pdf")
