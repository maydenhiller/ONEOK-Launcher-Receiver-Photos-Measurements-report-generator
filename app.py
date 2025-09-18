import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from PyPDF2 import PdfMerger
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

# Match directional images
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

# Create full-page image PDF
def full_page_image(image_file):
    img = Image.open(image_file).convert("RGB")
    output = io.BytesIO()
    img.save(output, format="PDF")
    return output.getvalue()

# Create directional page styled like template
def create_directional_page(job_name, title, image_file):
    base = Image.open(image_file).convert("RGB")
    W, H = base.size
    canvas = Image.new("RGB", (W, H + 200), "white")
    canvas.paste(base, (0, 200))

    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("arial.ttf", size=36)
    except:
        font = ImageFont.load_default()

    draw.text((W // 2, 40), job_name, font=font, anchor="mm", fill="black")
    draw.text((W // 2, 100), title, font=font, anchor="mm", fill="black")

    output = io.BytesIO()
    canvas.save(output, format="PDF")
    return output.getvalue()

# Generate full report
def generate_report(job_name, launcher_img, receiver_img, launcher_views, receiver_views):
    merger = PdfMerger()

    # Page 1: Launcher.jpg full-page
    merger.append(io.BytesIO(full_page_image(launcher_img)))

    # Pages 2–9: Launcher directional views
    launcher_matched = match_directional_images(launcher_views, "launcher")
    for direction in direction_aliases:
        if direction in launcher_matched:
            title = f"Launcher {direction}"
            page = create_directional_page(job_name, title, launcher_matched[direction])
            merger.append(io.BytesIO(page))

    # Page 10: Receiver.jpg full-page
    merger.append(io.BytesIO(full_page_image(receiver_img)))

    # Pages 11–18: Receiver directional views
    receiver_matched = match_directional_images(receiver_views, "receiver")
    for direction in direction_aliases:
        if direction in receiver_matched:
            title = f"Receiver {direction}"
            page = create_directional_page(job_name, title, receiver_matched[direction])
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
