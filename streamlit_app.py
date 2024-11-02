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

def create_audio_from_text(text, lang='en'):
    tts = gTTS(text=text, lang=lang, slow=False)
    audio_path = "output_audio.mp3"
    tts.save(audio_path)
    return audio_path

def create_custom_text_image(text, size=(640, 480), font_size=24, color='black', position='bottom'):
    image = Image.new("RGB", size, (255, 255, 255))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    text_position = (10, size[1] - font_size - 10) if position == 'bottom' else (10, 10)
    draw.text(text_position, text, fill=color, font=font)
    return np.array(image)

def slide_effect(clip, duration, start_pos=(-clip.w, 0)):
    """Slide the clip in from the start position over the specified duration."""
    return clip.set_position(lambda t: (start_pos[0] + t * (clip.w / duration), start_pos[1]))

def zoom_effect(clip, duration, zoom_factor=1.2):
    """Zoom the clip in over the specified duration."""
    def make_frame(t):
        return clip.resize(1 + (zoom_factor - 1) * (t / duration)).get_frame(t)
    return VideoClip(make_frame, duration=duration)

def create_video_with_transitions(thumbnails, audio_path, durations, text_overlays, transition_effect):
    clips = []
    audio_clip = AudioFileClip(audio_path)
    total_duration = audio_clip.duration

    if thumbnails:
        persistent_thumbnail = ImageClip(thumbnails[0]).set_duration(total_duration)
        clips.append(persistent_thumbnail)

    for idx, thumbnail in enumerate(thumbnails):
        duration = durations[idx]
        image = ImageClip(thumbnail).set_duration(duration)

        if transition_effect == 'fade':
            image = fadein(image, 1).fadeout(1)
        elif transition_effect == 'slide':
            image = slide_effect(image, duration)
        elif transition_effect == 'zoom':
            image = zoom_effect(image, duration)

        if text_overlays and idx < len(text_overlays):
            text_image = create_custom_text_image(text_overlays[idx], size=image.size)
            text_clip = ImageClip(text_image).set_duration(duration).set_position('bottom')
            clips.append(text_clip)

        clips.append(image)

    video = concatenate_videoclips(clips, method="compose")
    return video.set_audio(audio_clip)

def add_background_effects(video, background_path):
    background = ImageClip(background_path).set_duration(video.duration)
    return CompositeVideoClip([background, video])

def add_watermark(video, watermark_path):
    watermark = ImageClip(watermark_path).set_duration(video.duration).set_position(("right", "bottom")).set_opacity(0.5)
    return CompositeVideoClip([video, watermark])

# Streamlit UI
st.title("Enhanced PDF to Video with Speech")

# File uploads
pdf_file = st.file_uploader("Upload a PDF file", type="pdf")
thumbnails = st.file_uploader("Upload thumbnail images", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
background_music = st.file_uploader("Upload background music (optional)", type=["mp3", "wav"])
background_image = st.file_uploader("Upload a background image (optional)", type=["png", "jpg", "jpeg"])
watermark_image = st.file_uploader("Upload a watermark image (optional)", type=["png", "jpg", "jpeg"])

# New feature: Custom Text Input for overlays
text_overlays = st.text_area("Enter custom text for overlays (one per thumbnail)").splitlines()

# Language selection for audio
language = st.selectbox("Select audio language:", ['en', 'es', 'fr', 'de'])

# Video speed control
playback_speed = st.slider("Select video playback speed:", 0.5, 2.0, 1.0)

# Select transition effect
transition_effect = st.selectbox("Select transition effect:", ['fade', 'slide', 'zoom'])

if pdf_file and thumbnails:
    if st.button("Generate Video"):
        # Read PDF text
        pdf_text = pdf_to_text(pdf_file)

        # Create audio from the text
        audio_path = create_audio_from_text(pdf_text, lang=language)

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

        # Create video with transitions and persistent thumbnail
        video = create_video_with_transitions(thumbnail_paths, audio_path, durations, text_overlays, transition_effect)

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

        # Add watermark if provided
        if watermark_image:
            watermark_path = os.path.join(temp_dir, "watermark.png")
            with open(watermark_path, "wb") as f:
                f.write(watermark_image.getbuffer())
            video = add_watermark(video, watermark_path)

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
        if watermark_image:
            os.remove(watermark_path)
else:
    st.warning("Please upload a PDF and thumbnail images to proceed.")
