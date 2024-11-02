import streamlit as st
from moviepy.editor import *
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

def create_audio_from_text(text):
    tts = gTTS(text=text, lang='en')
    audio_path = "output_audio.mp3"
    tts.save(audio_path)
    return audio_path

def create_text_image(text, size=(640, 480), font_size=24):
    # Create an image with white background
    image = Image.new("RGB", size, (255, 255, 255))
    draw = ImageDraw.Draw(image)

    # Use a default font
    font = ImageFont.load_default()
    draw.text((10, 10), text, fill="black", font=font)

    return np.array(image)

def create_video(thumbnails, audio_path, text_list, durations):
    clips = []
    
    for idx, thumbnail in enumerate(thumbnails):
        image = ImageClip(thumbnail).set_duration(durations[idx])  # Use specified duration for each thumbnail
        clips.append(image)

        # Create and add text overlay for each thumbnail
        text_image = create_text_image(text_list[idx], size=image.size)
        text_clip = ImageClip(text_image).set_duration(durations[idx]).set_position('bottom')
        clips.append(text_clip)

    # Combine all clips
    video = concatenate_videoclips(clips, method="compose")

    # Load audio and set it to the video
    audio = AudioFileClip(audio_path)
    video = video.set_audio(audio)

    return video

# Streamlit UI
st.title("Enhanced PDF to Video with Speech")

# File upload
pdf_file = st.file_uploader("Upload a PDF file", type="pdf")
thumbnails = st.file_uploader("Upload thumbnail images", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
background_music = st.file_uploader("Upload background music (optional)", type=["mp3", "wav"])

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
        text_list = []
        durations = []

        for thumbnail in thumbnails:
            thumbnail_path = os.path.join(temp_dir, thumbnail.name)
            with open(thumbnail_path, "wb") as f:
                f.write(thumbnail.getbuffer())
            thumbnail_paths.append(thumbnail_path)

            # Split the text into chunks for overlays
            text_list.append(pdf_text)  # You can customize this to split text more creatively
            durations.append(5)  # Default duration for each thumbnail, can be customized by user input

        # Create video
        video = create_video(thumbnail_paths, audio_path, text_list, durations)

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
else:
    st.warning("Please upload a PDF and thumbnail images to proceed.")
