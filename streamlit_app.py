import streamlit as st
import random
import os
from moviepy.editor import *
from moviepy.video.fx.all import fadein, fadeout, speedx
import fitz  # PyMuPDF
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import textwrap
import emoji

# Constants
CHARACTER_LIMIT = 2000
TEMP_DIR = "temp"

# Utility Functions
def pdf_to_text(pdf_file):
    """Extract text from a PDF file with a character limit."""
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
        if len(text) >= CHARACTER_LIMIT:
            break
    return text[:CHARACTER_LIMIT]

def create_audio_from_text(text, lang='en'):
    """Create audio from text using gTTS."""
    tts = gTTS(text=text, lang=lang, slow=False)
    audio_path = os.path.join(TEMP_DIR, "output_audio.mp3")
    tts.save(audio_path)
    return audio_path

def create_custom_text_image(text, size=(640, 480), font_size=24):
    """Create an image with custom text."""
    image = Image.new("RGB", size, (255, 255, 255))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    wrapped_text = textwrap.fill(text, width=30)
    draw.text((10, 10), wrapped_text, fill="black", font=font)
    return image

def create_video_with_transitions(thumbnails, audio_path, durations, text_overlays):
    """Create a video with transitions and audio."""
    clips = []
    audio_clip = AudioFileClip(audio_path)

    for idx, thumbnail in enumerate(thumbnails):
        duration = durations[idx]
        image = ImageClip(thumbnail).set_duration(duration).fx(fadein, 1).fx(fadeout, 1)

        if text_overlays and idx < len(text_overlays):
            text_image = create_custom_text_image(text_overlays[idx], size=image.size)
            text_image_path = os.path.join(TEMP_DIR, f"text_overlay_{idx}.png")
            text_image.save(text_image_path)
            text_clip = ImageClip(text_image_path).set_duration(duration).set_position('bottom')
            clips.append(text_clip)

        clips.append(image)

    video = concatenate_videoclips(clips, method="compose").set_audio(audio_clip)
    return video

def add_background_effects(video, background_path):
    """Add a background image to the video."""
    background = ImageClip(background_path).set_duration(video.duration)
    return CompositeVideoClip([background, video])

def create_image_collage(images, size=(1280, 720)):
    """Create a collage from a list of images."""
    collage = Image.new("RGB", size, (255, 255, 255))
    for idx, img in enumerate(images):
        image = Image.open(img).resize((200, 200))
        x_offset = (idx % 5) * 200
        y_offset = (idx // 5) * 200
        collage.paste(image, (x_offset, y_offset))
    return collage

def mix_audio_tracks(audio_paths):
    """Mix multiple audio tracks."""
    audio_clips = [AudioFileClip(path) for path in audio_paths]
    final_audio = concatenate_audioclips(audio_clips)
    return final_audio

def add_dynamic_speed(video, speed_segments):
    """Apply different speeds to different segments."""
    clips = []
    for start, end, speed in speed_segments:
        subclip = video.subclip(start, end).fx(speedx, speed)
        clips.append(subclip)
    return concatenate_videoclips(clips)

def apply_filter(image, filter_type):
    """Apply a filter to an image."""
    if filter_type == "Sepia":
        sepia_image = image.convert("RGB")
        width, height = sepia_image.size
        pixels = sepia_image.load()
        for py in range(height):
            for px in range(width):
                r, g, b = sepia_image.getpixel((px, py))
                tr = int(0.393 * r + 0.769 * g + 0.189 * b)
                tg = int(0.349 * r + 0.686 * g + 0.168 * b)
                tb = int(0.272 * r + 0.534 * g + 0.131 * b)
                pixels[px, py] = (min(tr, 255), min(tg, 255), min(tb, 255))
        return sepia_image
    elif filter_type == "Blur":
        return image.filter(ImageFilter.GaussianBlur(radius=5))
    return image

def overlay_random_shapes(image):
    """Overlay random shapes on the given image."""
    draw = ImageDraw.Draw(image)
    width, height = image.size
    num_shapes = random.randint(1, 5)
    for _ in range(num_shapes):
        shape_type = random.choice(['circle', 'rectangle'])
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(x1, width)
        y2 = random.randint(y1, height)
        color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 128)
        if shape_type == 'circle':
            draw.ellipse([x1, y1, x2, y2], fill=color)
        elif shape_type == 'rectangle':
            draw.rectangle([x1, y1, x2, y2], fill=color)
    return image

# Streamlit UI
st.set_page_config(page_title="🎬 Create Youtube Videos Effortlessly", layout="wide")
st.title("🎬 Sobarine Content Technologies 🌊")
st.markdown("<h2 style='color: #66ccff; text-align: center;'>Create Stunning Videos Effortlessly!</h2>", unsafe_allow_html=True)

# Main content
st.header("Upload Your Content")
pdf_file = st.file_uploader("Upload your PDF 📄 (max 2000 characters)", type="pdf")
thumbnails = st.file_uploader("Upload images 🖼️", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
background_music = st.file_uploader("Upload background music 🎶 (optional)", type=["mp3", "wav"])
background_image = st.file_uploader("Upload a background image 🖼️ (optional)", type=["png", "jpg", "jpeg"])

text_input = st.text_area("Paste your content (max 2000 characters)", max_chars=CHARACTER_LIMIT)
st.write(f"Characters used: {len(text_input)}")

text_overlays = st.text_area("Enter custom text for overlays (one per thumbnail)").splitlines()

# Generate Video Button
if (pdf_file or text_input) and thumbnails:
    if st.button("Generate Video!"):
        try:
            os.makedirs(TEMP_DIR, exist_ok=True)

            # Extract text
            input_text = pdf_to_text(pdf_file) if pdf_file else text_input
            audio_path = create_audio_from_text(input_text)
            thumbnail_paths = [os.path.join(TEMP_DIR, t.name) for t in thumbnails]

            # Create Video
            video = create_video_with_transitions(thumbnail_paths, audio_path, [5] * len(thumbnails), text_overlays)
            video_path = os.path.join(TEMP_DIR, "output_video.mp4")
            video.write_videofile(video_path, codec="libx264")

            # Display Video
            st.video(video_path)
        except Exception as e:
            st.error(f"An error occurred: {e}")
