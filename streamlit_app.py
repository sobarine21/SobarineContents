import streamlit as st
from moviepy.editor import *
import fitz  # PyMuPDF
import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np

def pdf_to_text(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def create_text_image(text, size=(640, 480), font_size=24):
    # Create an image with white background
    image = Image.new("RGB", size, (255, 255, 255))
    draw = ImageDraw.Draw(image)

    # Use a default font
    font = ImageFont.load_default()
    draw.text((10, 10), text, fill="black", font=font)

    # Convert to numpy array and then to ImageClip
    return ImageClip(np.array(image)).set_duration(5)

def create_video(pdf_text, thumbnails):
    clips = []
    
    for thumbnail in thumbnails:
        image = ImageClip(thumbnail).set_duration(2)  # 2 seconds for each thumbnail
        clips.append(image)

    # Create a text image
    text_image = create_text_image(pdf_text, size=(640, 480), font_size=24)
    clips.append(text_image)

    # Combine all clips
    video = concatenate_videoclips(clips, method="compose")
    
    return video

# Streamlit UI
st.title("PDF to Video Generator")

# File upload
pdf_file = st.file_uploader("Upload a PDF file", type="pdf")
thumbnails = st.file_uploader("Upload thumbnail images", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

# Ensure temp directory exists
temp_dir = "temp"
os.makedirs(temp_dir, exist_ok=True)

if pdf_file and thumbnails:
    if st.button("Generate Video"):
        # Read PDF text
        pdf_text = pdf_to_text(pdf_file)

        # Save thumbnails temporarily
        thumbnail_paths = []
        for thumbnail in thumbnails:
            thumbnail_path = os.path.join(temp_dir, thumbnail.name)
            with open(thumbnail_path, "wb") as f:
                f.write(thumbnail.getbuffer())
            thumbnail_paths.append(thumbnail_path)

        # Create video
        video = create_video(pdf_text, thumbnail_paths)

        # Save video
        video_path = "output_video.mp4"
        video.write_videofile(video_path, fps=24)

        st.success("Video generated successfully!")
        st.video(video_path)

        # Cleanup
        for path in thumbnail_paths:
            os.remove(path)
else:
    st.warning("Please upload a PDF and thumbnail images to proceed.")
