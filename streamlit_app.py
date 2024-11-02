import streamlit as st
import random
from moviepy.editor import *
from moviepy.video.fx.all import fadein, fadeout, speedx, colorx
import fitz
from gtts import gTTS
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import textwrap

# Utility Functions
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
    wrapped_text = textwrap.fill(text, width=30)
    draw.text((10, 10), wrapped_text, fill="black", font=font)
    return np.array(image)

def create_video_with_transitions(thumbnails, audio_path, durations, text_overlays):
    clips = []
    audio_clip = AudioFileClip(audio_path)

    for idx, thumbnail in enumerate(thumbnails):
        duration = durations[idx]
        image = ImageClip(thumbnail).set_duration(duration)
        image = fadein(image, 1).fadeout(1)

        if text_overlays and idx < len(text_overlays):
            text_image = create_custom_text_image(text_overlays[idx], size=image.size)
            text_clip = ImageClip(text_image).set_duration(duration).set_position('bottom')
            clips.append(text_clip)

        clips.append(image)

    video = concatenate_videoclips(clips, method="compose").set_audio(audio_clip)
    return video

def add_background_effects(video, background_path):
    background = ImageClip(background_path).set_duration(video.duration)
    return CompositeVideoClip([background, video])

# Dynamic blue-themed background color function
def get_blue_shade():
    shades_of_blue = ['#E0F7FA', '#B2EBF2', '#80DEEA', '#4DD0E1', '#26C6DA', '#00BCD4', '#00ACC1']
    return random.choice(shades_of_blue)

# Additional features
def overlay_random_shapes(image):
    draw = ImageDraw.Draw(image)
    for _ in range(random.randint(3, 10)):
        shape_type = random.choice(['circle', 'rectangle'])
        color = random_color()
        if shape_type == 'circle':
            radius = random.randint(10, 50)
            x = random.randint(radius, image.size[0] - radius)
            y = random.randint(radius, image.size[1] - radius)
            draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill=color, outline=color)
        else:
            x1, y1 = random.randint(0, image.size[0]), random.randint(0, image.size[1])
            x2, y2 = random.randint(x1, image.size[0]), random.randint(y1, image.size[1])
            draw.rectangle((x1, y1, x2, y2), fill=color, outline=color)
    return np.array(image)

def random_color():
    return tuple(random.randint(0, 255) for _ in range(3))

# Streamlit UI
st.set_page_config(page_title="🎬 YouTube Video Creator", layout="wide")
st.title("🎬 YouTube Video Creator 🌊")
st.markdown("<h2 style='color: #003366; text-align: center;'>Create Stunning Videos Effortlessly!</h2>", unsafe_allow_html=True)

# Set dynamic blue background color
background_color = get_blue_shade()
st.markdown(f"<style>body {{ background-color: {background_color}; }}</style>", unsafe_allow_html=True)

# Main content
st.header("Upload Your Content")
pdf_file = st.file_uploader("Upload your PDF 📄", type="pdf")
thumbnails = st.file_uploader("Upload images 🖼️", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
background_music = st.file_uploader("Upload background music 🎶 (optional)", type=["mp3", "wav"])
background_image = st.file_uploader("Upload a background image 🖼️ (optional)", type=["png", "jpg", "jpeg"])
watermark_image = st.file_uploader("Upload a watermark image (optional)", type=["png", "jpg", "jpeg"])
sound_effects = st.file_uploader("Upload sound effects (optional)", type=["mp3", "wav"], accept_multiple_files=True)

st.header("Customize Your Video")
text_overlays = st.text_area("Enter custom text for overlays (one per thumbnail)").splitlines()
apply_shapes = st.checkbox("Overlay random shapes on images")
apply_glitch = st.checkbox("Apply glitch effect on video")

# Video speed control
playback_speed = st.slider("Select video playback speed:", 0.5, 2.0, 1.0)

# Generate Video Button
if pdf_file and thumbnails:
    if st.button("Generate Video!"):
        try:
            # Read PDF text
            pdf_text = pdf_to_text(pdf_file)

            # Create audio from the text
            audio_path = create_audio_from_text(pdf_text)
            audio_clip = AudioFileClip(audio_path)

            # Check audio duration
            audio_duration = audio_clip.duration
            if audio_duration == 0:
                st.error("The generated audio file is empty. Please check the input text.")
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
                if apply_shapes:
                    # Overlay random shapes if the option is checked
                    img_array = overlay_random_shapes(np.array(Image.open(thumbnail_path)))
                    img_with_shapes_path = os.path.join(temp_dir, "shaped_" + thumbnail.name)
                    Image.fromarray(img_array).save(img_with_shapes_path)
                    thumbnail_paths.append(img_with_shapes_path)
                else:
                    thumbnail_paths.append(thumbnail_path)

            # Create video with transitions
            video = create_video_with_transitions(thumbnail_paths, audio_path, durations, text_overlays)

            # Trim video if it exceeds audio duration
            if video.duration > audio_duration:
                video = video.subclip(0, audio_duration)

            # Adjust playback speed
            video = video.fx(speedx, playback_speed)

            # Add background effects if provided
            if background_image:
                bg_path = os.path.join(temp_dir, "background_image.jpg")
                with open(bg_path, "wb") as f:
                    f.write(background_image.getbuffer())
                video = add_background_effects(video, bg_path)

            # Add watermark if provided
            if watermark_image:
                watermark_path = os.path.join(temp_dir, "watermark.png")
                with open(watermark_path, "wb") as f:
                    f.write(watermark_image.getbuffer())
                video = CompositeVideoClip([video, ImageClip(watermark_path).set_duration(video.duration).set_position(("right", "bottom")).set_opacity(0.5)])

            # Add sound effects if provided
            if sound_effects:
                effect_paths = []
                for effect in sound_effects:
                    effect_path = os.path.join(temp_dir, effect.name)
                    with open(effect_path, "wb") as f:
                        f.write(effect.getbuffer())
                    effect_paths.append(effect_path)
                video = add_sound_effects(video, effect_paths)

            # Apply glitch effect if checked
            if apply_glitch:
                video = apply_glitch_effect(video)

            # Save video
            video_path = "output_video.mp4"
            video.write_videofile(video_path, fps=24)

            st.success("Video generated successfully!")
            st.video(video_path)

        except Exception as e:
            st.error(f"An error occurred while generating the video: {e}")

        finally:
            # Cleanup
            if os.path.exists(audio_path):
                os.remove(audio_path)
            for path in thumbnail_paths:
                if os.path.exists(path):
                    os.remove(path)
            if watermark_image and os.path.exists(watermark_path):
                os.remove(watermark_path)
            if background_music and os.path.exists(bg_music_path):
                os.remove(bg_music_path)
            if background_image and os.path.exists(bg_path):
                os.remove(bg_path)
            if sound_effects:
                for effect in effect_paths:
                    if os.path.exists(effect):
                        os.remove(effect)

else:
    st.warning("Please upload a PDF and thumbnail images to proceed.")
