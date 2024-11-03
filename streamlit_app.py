import streamlit as st
import random
from moviepy.editor import *
from moviepy.video.fx.all import fadein, fadeout, speedx
import fitz
from gtts import gTTS
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import textwrap
import emoji

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
    return image

def create_video_with_transitions(thumbnails, audio_path, durations, text_overlays):
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
    background = ImageClip(background_path).set_duration(video.duration)
    return CompositeVideoClip([background, video])

def random_color():
    return tuple(random.randint(0, 255) for _ in range(3))

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
    return image

def text_to_emoji(text):
    return emoji.emojize(text, use_aliases=True)

def apply_filter(image, filter_type):
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

# Streamlit UI
st.set_page_config(page_title="🎬 YouTube Video Creator", layout="wide")
st.title("🎬 YouTube Video Creator 🌊")
st.markdown("<h2 style='color: #003366; text-align: center;'>Create Stunning Videos Effortlessly!</h2>", unsafe_allow_html=True)

# Main content
st.header("Upload Your Content")
pdf_file = st.file_uploader("Upload your PDF 📄", type="pdf")
thumbnails = st.file_uploader("Upload images 🖼️", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
background_music = st.file_uploader("Upload background music 🎶 (optional)", type=["mp3", "wav"])
background_image = st.file_uploader("Upload a background image 🖼️ (optional)", type=["png", "jpg", "jpeg"])
watermark_image = st.file_uploader("Upload a watermark image (optional)", type=["png", "jpg", "jpeg"])
sound_effects = st.file_uploader("Upload sound effects (optional)", type=["mp3", "wav"], accept_multiple_files=True)

# Text input with character limit
text_input = st.text_area("Paste your content (max 2000 characters)", max_chars=2000)
st.write(f"Characters used: {len(text_input)}")

# Video customization options
st.header("Customize Your Video")
text_overlays = st.text_area("Enter custom text for overlays (one per thumbnail)").splitlines()
apply_shapes = st.checkbox("Overlay random shapes on images")
apply_glitch = st.checkbox("Apply glitch effect on video")
filter_option = st.selectbox("Select an image filter for thumbnails:", ["None", "Sepia", "Blur"])

# Video speed control
playback_speed = st.slider("Select video playback speed:", 0.5, 2.0, 1.0)

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
            # Use text from the PDF if available, otherwise use pasted content
            if pdf_file:
                pdf_text = pdf_to_text(pdf_file)
            else:
                pdf_text = text_input

            # Convert text to emojis
            pdf_text = text_to_emoji(pdf_text)

            # Create audio from the text
            audio_path = create_audio_from_text(pdf_text)
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

                if apply_shapes:
                    img = Image.open(thumbnail_path)
                    img_with_shapes = overlay_random_shapes(img)
                    img_with_shapes_path = os.path.join(temp_dir, "shaped_" + thumbnail.name)
                    img_with_shapes.save(img_with_shapes_path)
                    thumbnail_paths.append(img_with_shapes_path)
                else:
                    thumbnail_paths.append(thumbnail_path)

                # Apply selected filter if any
                if filter_option != "None":
                    img = Image.open(thumbnail_path)
                    img = apply_filter(img, filter_option)
                    img.save(thumbnail_path)  # Overwrite with filtered image

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
                for effect in sound_effects:
                    effect_path = os.path.join(temp_dir, effect.name)
                    with open(effect_path, "wb") as f:
                        f.write(effect.getbuffer())
                    effect_paths.append(effect_path)

            # Save video
            video_path = "output_video.mp4"
            video.write_videofile(video_path, fps=24)

            st.success("Video generated successfully!")
            st.video(video_path)

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
