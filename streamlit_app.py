import streamlit as st
from moviepy.editor import *
from moviepy.video.fx.all import fadein, fadeout
import fitz
from gtts import gTTS
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Function Definitions (remains the same)

# Custom CSS for styling
st.markdown("""
    <style>
    body {
        background-color: #f0f8ff;
        font-family: 'Helvetica Neue', sans-serif;
    }
    .title {
        color: #ff4500;
        text-align: center;
    }
    .sidebar .sidebar-content {
        background-color: #ffebcd;
        border-radius: 10px;
        padding: 20px;
    }
    .stButton > button {
        background-color: #ff6347;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 10px 20px;
        font-size: 16px;
    }
    .stButton > button:hover {
        background-color: #ff4500;
    }
    .warning {
        color: #ff4500;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Streamlit UI
st.title("🎬 **Epic YouTube Video Creator** 🌈")
st.markdown("<h2 class='title'>Create Stunning Videos in Seconds!</h2>", unsafe_allow_html=True)

# Sidebar
st.sidebar.header("✨ Upload Your Content")
pdf_file = st.sidebar.file_uploader("Upload your PDF 📄", type="pdf")
thumbnails = st.sidebar.file_uploader("Upload images 🖼️", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
background_music = st.sidebar.file_uploader("Upload background music 🎶 (optional)", type=["mp3", "wav"])
background_image = st.sidebar.file_uploader("Upload a background image 🖼️ (optional)", type=["png", "jpg", "jpeg"])

st.sidebar.header("📝 Customize Your Video")
text_overlays = st.sidebar.text_area("Enter custom text for overlays (one per thumbnail)").splitlines()

# Video speed control
playback_speed = st.sidebar.slider("Select video playback speed:", 0.5, 2.0, 1.0)

# Generate Video Button
if pdf_file and thumbnails:
    if st.sidebar.button("🎬 **Generate Video!** 🎉"):
        try:
            # Read PDF text
            pdf_text = pdf_to_text(pdf_file)

            # Create audio from the text
            audio_path = create_audio_from_text(pdf_text)
            audio_clip = AudioFileClip(audio_path)

            # Check audio duration
            audio_duration = audio_clip.duration
            if audio_duration == 0:
                st.error("🚨 The generated audio file is empty. Please check the input text.")
                st.stop()

            # Save thumbnails temporarily
            temp_dir = "temp"
            os.makedirs(temp_dir, exist_ok=True)
            thumbnail_paths = []
            durations = [5] * len(thumbnails)

            for thumbnail in thumbnails:
                thumbnail_path = os.path.join(temp_dir, thumbnail.name)
                with open(thumbnail_path, "wb") as f:
                    f.write(thumbnail.getbuffer())
                thumbnail_paths.append(thumbnail_path)

            # Create video with transitions
            video = create_video_with_transitions(thumbnail_paths, audio_path, durations, text_overlays)

            # Trim video if it exceeds audio duration
            if video.duration > audio_duration:
                video = video.subclip(0, audio_duration)

            # Adjust playback speed
            video = video.fx(vfx.speedx, playback_speed)

            # Add background effects if provided
            if background_image:
                bg_path = os.path.join(temp_dir, "background_image.jpg")
                with open(bg_path, "wb") as f:
                    f.write(background_image.getbuffer())
                video = add_background_effects(video, bg_path)

            # Add background music if provided
            if background_music:
                bg_music_path = os.path.join(temp_dir, "background_music.mp3")
                with open(bg_music_path, "wb") as f:
                    f.write(background_music.getbuffer())
                bg_audio = AudioFileClip(bg_music_path)
                video = video.set_audio(CompositeAudioClip([video.audio, bg_audio]))

            # Save video
            video_path = "output_video.mp4"
            video.write_videofile(video_path, fps=24)

            st.success("🎉 Video generated successfully! 🎬")
            st.video(video_path)

        except Exception as e:
            st.error(f"🚨 An error occurred while generating the video: {e}")

        finally:
            # Cleanup
            if os.path.exists(audio_path):
                os.remove(audio_path)
            for path in thumbnail_paths:
                if os.path.exists(path):
                    os.remove(path)
            if background_music and os.path.exists(bg_music_path):
                os.remove(bg_music_path)
            if background_image and os.path.exists(bg_path):
                os.remove(bg_path)

else:
    st.warning("⚠️ **Please upload a PDF and thumbnail images to proceed.**", unsafe_allow_html=True)
