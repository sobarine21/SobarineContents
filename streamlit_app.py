import streamlit as st
from moviepy.editor import *
import fitz  # PyMuPDF
from gtts import gTTS
import os
import numpy as np

def pdf_to_text(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def create_audio_from_text(text):
    tts = gTTS(text=text, lang='en')
    audio_path = "output_audio.mp3"
    tts.save(audio_path)
    return audio_path

def create_video(thumbnails, audio_path):
    clips = []
    
    for thumbnail in thumbnails:
        image = ImageClip(thumbnail).set_duration(5)  # 5 seconds for each thumbnail
        clips.append(image)

    # Combine all clips
    video = concatenate_videoclips(clips, method="compose")

    # Load audio and set it to the video
    audio = AudioFileClip(audio_path)
    video = video.set_audio(audio)

    return video

# Streamlit UI
st.title("PDF to Video with Speech")

# File upload
pdf_file = st.file_uploader("Upload a PDF file", type="pdf")
thumbnails = st.file_uploader("Upload thumbnail images", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

if pdf_file and thumbnails:
    if st.button("Generate Video"):
        # Read PDF text
        pdf_text = pdf_to_text(pdf_file)

        # Create audio from the text
        audio_path = create_audio_from_text(pdf_text)

        # Save thumbnails temporarily
        temp_dir = "temp"
        os.makedirs(temp_dir, exist_ok=True)
        thumbnail_paths = []
        for thumbnail in thumbnails:
            thumbnail_path = os.path.join(temp_dir, thumbnail.name)
            with open(thumbnail_path, "wb") as f:
                f.write(thumbnail.getbuffer())
            thumbnail_paths.append(thumbnail_path)

        # Create video
        video = create_video(thumbnail_paths, audio_path)

        # Save video
        video_path = "output_video.mp4"
        video.write_videofile(video_path, fps=24)

        st.success("Video generated successfully!")
        st.video(video_path)

        # Cleanup
        os.remove(audio_path)
        for path in thumbnail_paths:
            os.remove(path)
else:
    st.warning("Please upload a PDF and thumbnail images to proceed.")
