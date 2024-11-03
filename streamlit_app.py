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
    audio_path = "output_audio.mp3"
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
            text_image_path = "temp_text_image.png"
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

def convert_text_to_emojis(text):
    """Convert text to emojis."""
    return emoji.emojize(text, use_aliases=True)

def share_video_on_socials(video_path):
    """Provide links to share the video."""
    st.write("Share your video:")
    st.write(f"[Twitter](https://twitter.com/intent/tweet?url={video_path})")
    st.write(f"[Facebook](https://www.facebook.com/sharer/sharer.php?u={video_path})")

def overlay_random_shapes(image):
    """Overlay random shapes on the given image."""
    draw = ImageDraw.Draw(image)
    width, height = image.size

    # Define number of shapes to overlay
    num_shapes = random.randint(1, 5)
    
    for _ in range(num_shapes):
        shape_type = random.choice(['circle', 'rectangle'])
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(x1, width)
        y2 = random.randint(y1, height)

        if shape_type == 'circle':
            draw.ellipse([x1, y1, x2, y2], fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 128))
        elif shape_type == 'rectangle':
            draw.rectangle([x1, y1, x2, y2], fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), 128))

    return image

# Streamlit UI
st.set_page_config(page_title="🎬 Create Youtube Videos effortlesly", layout="wide")
st.title("🎬 Sobarine Content Technologies 🌊")
st.markdown("<h2 style='color: #66ccff; text-align: center;'>Create Stunning Videos Effortlessly!</h2>", unsafe_allow_html=True)

# Main content
st.header("Upload Your Content")
pdf_file = st.file_uploader("Upload your PDF 📄 (max 2000 characters)", type="pdf")
thumbnails = st.file_uploader("Upload images 🖼️", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
background_music = st.file_uploader("Upload background music 🎶 (optional)", type=["mp3", "wav"], accept_multiple_files=True)
background_image = st.file_uploader("Upload a background image 🖼️ (optional)", type=["png", "jpg", "jpeg"])
watermark_image = st.file_uploader("Upload a watermark image (optional)", type=["png", "jpg", "jpeg"])
sound_effects = st.file_uploader("Upload sound effects (optional)", type=["mp3", "wav"], accept_multiple_files=True)

# Text input with character limit
text_input = st.text_area("Paste your content (max 2000 characters)", max_chars=CHARACTER_LIMIT)
st.write(f"Characters used: {len(text_input)}")

# Video customization options
st.header("Customize Your Video")
text_overlays = st.text_area("Enter custom text for overlays (one per thumbnail)").splitlines()
apply_shapes = st.checkbox("Overlay random shapes on images")
apply_glitch = st.checkbox("Apply glitch effect on video")
filter_option = st.selectbox("Select an image filter for thumbnails:", ["None", "Sepia", "Blur"])
language_option = st.selectbox("Select TTS language:", ['en', 'es', 'fr', 'de', 'it'])

# Image collage option
if st.checkbox("Create an image collage"):
    collage = create_image_collage(thumbnails)
    collage_path = "collage.png"
    collage.save(collage_path)
    st.image(collage_path, caption='Generated Collage', use_column_width=True)

# Dynamic speed control
dynamic_speed = st.checkbox("Add dynamic speed to video segments")
speed_segments = []
if dynamic_speed:
    segment_count = st.number_input("How many speed segments?", min_value=1, max_value=5, value=1)
    for i in range(segment_count):
        start_time = st.number_input(f"Start time for segment {i+1} (seconds)", value=0)
        end_time = st.number_input(f"End time for segment {i+1} (seconds)", value=5)
        speed = st.number_input(f"Speed for segment {i+1} (e.g., 1.0 for normal, 2.0 for double speed)", value=1.0)
        speed_segments.append((start_time, end_time, speed))

# Initialize paths
audio_path = None
watermark_path = None
bg_path = None
temp_dir = "temp"
thumbnail_paths = []
effect_paths = []

# Generate Video Button
if (pdf_file or text_input) and thumbnails:
    if st.button("Generate Video!"):
        try:
            # Read PDF text or use input text
            pdf_text = pdf_to_text(pdf_file) if pdf_file else ""
            input_text = pdf_text if pdf_text else text_input
            if not input_text:
                st.error("Please provide content to generate audio.")
                st.stop()

            # Create audio from the text
            audio_path = create_audio_from_text(input_text, lang=language_option)
            audio_clip = AudioFileClip(audio_path)

            # Check audio duration
            audio_duration = audio_clip.duration
            if audio_duration == 0:
                st.error("The generated audio file is empty. Please check the input text.")
                st.stop()

            os.makedirs(temp_dir, exist_ok=True)
            durations = [5] * len(thumbnails)

            for thumbnail in thumbnails:
                thumbnail_path = os.path.join(temp_dir, thumbnail.name)
                with open(thumbnail_path, "wb") as f:
                    f.write(thumbnail.getbuffer())

                # Apply selected filter
                if filter_option != "None":
                    img = Image.open(thumbnail_path)
                    img = apply_filter(img, filter_option)
                    img.save(thumbnail_path)

                if apply_shapes:
                    img_with_shapes = overlay_random_shapes(img)
                    img_with_shapes_path = os.path.join(temp_dir, "shaped_" + thumbnail.name)
                    img_with_shapes.save(img_with_shapes_path)
                    thumbnail_paths.append(img_with_shapes_path)
                else:
                    thumbnail_paths.append(thumbnail_path)

            # Create video with transitions
            video = create_video_with_transitions(thumbnail_paths, audio_path, durations, text_overlays)

            # Trim video if it exceeds audio duration
            if video.duration > audio_duration:
                video = video.subclip(0, audio_duration)

            # Adjust dynamic speed if selected
            if dynamic_speed:
                video = add_dynamic_speed(video, speed_segments)

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
                for effect in sound_effects:
                    effect_path = os.path.join(temp_dir, effect.name)
                    with open(effect_path, "wb") as f:
                        f.write(effect.getbuffer())
                    effect_paths.append(effect_path)
                # Mix sound effects
                mixed_audio = mix_audio_tracks(effect_paths)
                video = video.set_audio(mixed_audio)

            # Save video
            video_path = "output_video.mp4"
            video.write_videofile(video_path, fps=24)

            st.success("Video generated successfully!")
            st.video(video_path)
            share_video_on_socials(video_path)

        except Exception as e:
            st.error(f"An error occurred while generating the video: {e}")

        finally:
            # Cleanup
            if audio_path and os.path.exists(audio_path):
                os.remove(audio_path)
            for path in thumbnail_paths:
                if os.path.exists(path):
                    os.remove(path)
            if watermark_path and os.path.exists(watermark_path):
                os.remove(watermark_path)
            if bg_path and os.path.exists(bg_path):
                os.remove(bg_path)
            for effect in effect_paths:
                if os.path.exists(effect):
                    os.remove(effect)

else:
    st.warning("Please upload a PDF or paste content, and add thumbnail images to proceed.")
