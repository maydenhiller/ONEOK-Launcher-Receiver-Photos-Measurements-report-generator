import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from PyPDF2 import PdfMerger
import fitz
import io
import os

# Strict mapping of page order to allowed filenames (lowercase for matching)
launcher_order = [
    ["launcher.jpg"],  # Page 1
    ["launcher east.jpg", "launcher e.jpg", "launch e.jpg", "le.jpg"],  # Page 2
    ["launcher northeast.jpg", "launcher ne.jpg", "launch ne.jpg", "lne.jpg"],  # Page 3
    ["launcher north.jpg", "launcher n.jpg", "launch n.jpg", "ln.jpg"],  # Page 4
    ["launcher northwest.jpg", "launcher nw.jpg", "launch nw.jpg", "lnw.jpg"],  # Page 5
    ["launcher west.jpg", "launcher w.jpg", "launch w.jpg", "lw.jpg"],  # Page 6
    ["launcher southwest.jpg", "launcher sw.jpg", "launch sw.jpg", "lsw.jpg"],  # Page 7
    ["launcher south.jpg", "launcher s.jpg", "launch s.jpg", "ls.jpg"],  # Page 8
    ["launcher southeast.jpg", "launcher se.jpg", "launch se.jpg", "lse.jpg"],  # Page 9
]

receiver_order = [
    ["receiver.jpg"],  # Page 10
    ["receiver east.jpg", "receiver e.jpg", "re.jpg"],  # Page 11
    ["receiver northeast.jpg", "receiver ne.jpg", "rne.jpg"],  # Page 12
    ["receiver north.jpg", "receiver n.jpg", "rn.jpg"],  # Page 13
    ["receiver northwest.jpg", "receiver nw.jpg", "rnw.jpg"],  # Page 14
    ["receiver west.jpg", "receiver w.jpg", "rw.jpg"],  # Page 15
    ["receiver southwest.jpg", "receiver sw.jpg", "rsw.jpg"],  # Page 16
    ["receiver south.jpg", "receiver s.jpg", "rs.jpg"],  # Page 17
    ["receiver southeast.jpg", "receiver se.jpg", "rse.jpg"],  # Page 18
]

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

def find_file(files, allowed_names):
    allowed = [name.lower() for name in allowed_names]
    for f in files:
        if f.name.lower() in allowed:
            return f
    return None

def generate_report(job_name, all_images, template_pdf):
    template_img = extract_template_image(template_pdf)
    merger = PdfMerger()

    # Launcher pages
    for idx, allowed_names in enumerate(launcher_order, start=1):
        f = find_file(all_images, allowed_names)
        if not f:
            raise FileNotFoundError(f"Missing file for Launcher page {idx}: one of {allowed_names}")
        if idx == 1:
            merger.append(io.BytesIO(full_page_image(f)))
        else:
            # Capitalize only the first letter of the direction
            direction = allowed_names[0].split()[1].replace('.jpg', '').capitalize()
            title = f"Launcher {direction}"
            page = create_directional_page(template_img, job_name, title, f)
            merger.append(io.BytesIO(page))

    # Receiver pages
    for idx, allowed_names in enumerate(receiver_order, start=10):
        f = find_file(all_images, allowed_names)
        if not f:
            raise FileNotFoundError(f"Missing file for Receiver page {idx}: one of {allowed_names}")
        if idx == 10:
            merger.append(io.BytesIO(full_page_image(f)))
        else:
            # Capitalize only the first letter of the direction
            direction = allowed_names[0].split()[1].replace('.jpg', '').capitalize()
            title = f"Receiver {direction}"
            page = create_directional_page(template_img, job_name, title, f)
            merger.append(io.BytesIO(page))

    buf = io.BytesIO()
    merger.write(buf)
    merger.close()
    return buf

# Streamlit UI
st.set_page_config(page_title="Strict 18-Page Report Generator", layout="centered")
st.title("📄 Strict 18-Page Report Generator")

job_name = st.text_input("Enter Job Name")
template_pdf = st.file_uploader("Upload Template PDF", type=["pdf"])
all_images = st.file_uploader("Upload All 18 Images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

if st.button("Generate Report"):
    try:
        if not job_name or not template_pdf or not all_images or len(all_images) != 18:
            st.error("Please upload the template PDF, exactly 18 images, and enter a job name.")
        else:
            report = generate_report(job_name, all_images, template_pdf)
            st.success("✅ Report generated successfully!")
            st.download_button("📥 Download Report", data=report, file_name="Final_Report.pdf", mime="application/pdf")
    except Exception as e:
        st.error(f"Error: {e}")
