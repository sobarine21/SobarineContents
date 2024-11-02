import streamlit as st
from moviepy.editor import *
from moviepy.video.fx.all import fadein, fadeout  # Import fadein and fadeout
import fitz  # PyMuPDF
from gtts import gTTS
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def pdf_to_text(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def create_audio_from_text(text, lang='en'):
    tts = gTTS(text=text, lang=lang, slow=False)
    audio_path = "output_audio.mp3"
    tts.save(audio_path)
    return audio_path

def create_custom_text_image(text, size=(640, 480), font_size=24):
    image = Image.new("RGB", size, (255, 255, 255))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    draw.text((10, 10), text, fill="black", font=font)
    return np.array(image)

def create_video_with_transitions(thumbnails, audio_path, durations, transition_type='fade'):
    clips = []
    
    for idx, thumbnail in enumerate(thumbnails):
        image = ImageClip(thumbnail).set_duration(durations[idx])
        
        # Apply transitions
        if transition_type == 'fade':
            image = fadein(image, 1).fadeout(1)
        
        clips.append(image)

    video = concatenate_videoclips(clips, method="compose")
    audio = AudioFileClip(audio_path)
    return video.set_audio(audio)

def add_background_effects(video, background_path):
    background = ImageClip(background_path).set_duration(video.duration)
    return CompositeVideoClip([background, video])

# Streamlit UI
st.title("Enhanced PDF to Video with Speech")

# File uploads
pdf_file = st.file_uploader("Upload a PDF file", type="pdf")
thumbnails = st.file_uploader("Upload thumbnail images", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
background_music = st.file_uploader("Upload background music (optional)", type=["mp3", "wav"])
background_image = st.file_uploader("Upload a background image (optional)", type=["png", "jpg", "jpeg"])

# New feature: Custom Text Input
text_overlays = st.text_area("Enter custom text for overlays (one per thumbnail)")

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
        durations = [5] * len(thumbnails)  # Default duration for each thumbnail

        for thumbnail in thumbnails:
            thumbnail_path = os.path.join(temp_dir, thumbnail.name)
            with open(thumbnail_path, "wb") as f:
                f.write(thumbnail.getbuffer())
            thumbnail_paths.append(thumbnail_path)

        # Create video with transitions
        video = create_video_with_transitions(thumbnail_paths, audio_path, durations)

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

        st.success("Video generated successfully!")
        st.video(video_path)

        # Cleanup
        os.remove(audio_path)
        for path in thumbnail_paths:
            os.remove(path)
        if background_music:
            os.remove(bg_music_path)
        if background_image:
            os.remove(bg_path)
else:
    st.warning("Please upload a PDF and thumbnail images to proceed.")
