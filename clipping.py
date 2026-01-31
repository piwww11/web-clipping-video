import streamlit as st
import yt_dlp
import whisper
from groq import Groq
try:
    from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
except ImportError:
    import os
    os.environ['IMAGEIO_FFMPEG_EXE'] = 'ffmpeg'
    from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
import json
import tempfile
import traceback
import time
import numpy as np
from pathlib import Path

# Page config
st.set_page_config(
    page_title="AI Video Clipper Pro",
    page_icon="✂️",
    layout="wide"
)

# Helper function for smart cropping
def smart_crop(clip, target_aspect_ratio, min_crop_factor=0.7):
    """
    Smart cropping that preserves more of the frame
    min_crop_factor: minimum percentage of original frame to keep (0.7 = keep 70%)
    """
    w, h = clip.size
    target_w, target_h = target_aspect_ratio
    target_ratio = target_w / target_h
    current_ratio = w / h
    
    if abs(current_ratio - target_ratio) < 0.01:
        return clip  # Already correct ratio
    
    if current_ratio > target_ratio:
        # Video is wider - crop width (vertical video from landscape)
        new_w = int(h * target_ratio)
        
        # Don't crop more than necessary - use min_crop_factor
        max_crop_w = int(w * min_crop_factor)
        new_w = max(new_w, max_crop_w)
        
        # Center crop with slight bias toward center-right (where speakers often are)
        x_center = int(w * 0.55)  # Slight right bias instead of exact center
        x1 = max(0, min(x_center - new_w // 2, w - new_w))
        
        return clip.crop(x1=x1, x2=x1 + new_w)
    else:
        # Video is taller - crop height
        new_h = int(w / target_ratio)
        
        # Don't crop more than necessary
        max_crop_h = int(h * min_crop_factor)
        new_h = max(new_h, max_crop_h)
        
        # Crop from top (preserve upper part where face usually is)
        y1 = int(h * 0.15)  # Start crop 15% from top
        y2 = min(y1 + new_h, h)
        y1 = max(0, y2 - new_h)
        
        return clip.crop(y1=y1, y2=y2)

# Helper function for styled subtitles
def create_subtitle_clip(text, duration, video_size, style):
    """Create a styled subtitle TextClip"""
    
    styles = {
        "Bold Yellow (TikTok)": {
            'fontsize': 50,
            'color': 'yellow',
            'stroke_color': 'black',
            'stroke_width': 3,
            'font': 'Arial-Bold'
        },
        "White Shadow": {
            'fontsize': 45,
            'color': 'white',
            'stroke_color': 'black',
            'stroke_width': 2,
            'font': 'Arial-Bold'
        },
        "Black Outline": {
            'fontsize': 48,
            'color': 'white',
            'stroke_color': 'black',
            'stroke_width': 4,
            'font': 'Impact'
        },
        "Neon Glow": {
            'fontsize': 46,
            'color': '#00FF00',
            'stroke_color': '#00FFFF',
            'stroke_width': 2,
            'font': 'Arial-Bold'
        },
        "Gradient Pop": {
            'fontsize': 52,
            'color': '#FF1493',
            'stroke_color': '#FFD700',
            'stroke_width': 3,
            'font': 'Arial-Bold'
        }
    }
    
    config = styles.get(style, styles["Bold Yellow (TikTok)"])
    
    try:
        txt_clip = TextClip(
            text,
            fontsize=config['fontsize'],
            color=config['color'],
            stroke_color=config['stroke_color'],
            stroke_width=config['stroke_width'],
            font=config['font'],
            method='caption',
            size=(video_size[0] * 0.9, None),
            align='center'
        ).set_duration(duration)
        
        return txt_clip
    except Exception as e:
        st.warning(f"Subtitle rendering issue: {str(e)}")
        return None

# Title
st.title("✂️ AI Video Clipper Pro")
st.markdown("**Advanced AI-powered video clipper with smart features**")

# Metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("🎯 Max Clips", "1-10")
with col2:
    st.metric("📐 Formats", "5 Ratios")
with col3:
    st.metric("🎥 Quality", "HD/1080p")
with col4:
    st.metric("✂️ Smart Crop", "Face-Aware")

# Sidebar
with st.sidebar:
    st.header("🔑 API Configuration")
    api_key = st.text_input(
        "Groq API Key",
        type="password",
        help="Get free key: https://console.groq.com/keys"
    )
    
    st.markdown("---")
    st.header("⚙️ Quality Settings")
    
    video_quality = st.select_slider(
        "🎥 Output Quality",
        options=["Good (Fast)", "High (Balanced)", "Ultra (Slow)"],
        value="High (Balanced)",
        help="Higher quality = larger file size & slower processing"
    )
    
    # Map quality to encoding settings
    quality_presets = {
        "Good (Fast)": {'bitrate': '3000k', 'crf': '23', 'preset': 'fast'},
        "High (Balanced)": {'bitrate': '5000k', 'crf': '18', 'preset': 'medium'},
        "Ultra (Slow)": {'bitrate': '8000k', 'crf': '15', 'preset': 'slow'}
    }
    quality_settings = quality_presets[video_quality]
    
    st.markdown("---")
    st.header("🎬 Clip Settings")
    
    # Max clips
    max_clips = st.slider(
        "🎯 Number of Clips",
        min_value=1,
        max_value=10,
        value=3,
        help="How many clips to generate"
    )
    
    # Aspect ratio
    aspect_ratio = st.selectbox(
        "📐 Aspect Ratio",
        [
            "Original (No Crop)",
            "16:9 (YouTube)",
            "9:16 (TikTok/Reels)",
            "1:1 (Instagram)",
            "4:5 (Instagram Portrait)"
        ],
        index=0
    )
    
    # Crop quality settings
    if aspect_ratio != "Original (No Crop)":
        st.markdown("**🎨 Crop Settings:**")
        
        crop_aggressiveness = st.select_slider(
            "Crop Tightness",
            options=["Loose (Keep More Frame)", "Balanced", "Tight (Zoom More)"],
            value="Balanced",
            help="Loose = minimal zoom, keeps more context. Tight = more zoom, fills frame."
        )
        
        # Map to min_crop_factor
        crop_factor_map = {
            "Loose (Keep More Frame)": 0.80,  # Keep 80% of frame minimum
            "Balanced": 0.70,  # Keep 70% of frame minimum
            "Tight (Zoom More)": 0.60  # Keep 60% of frame minimum
        }
        crop_factor = crop_factor_map[crop_aggressiveness]
    else:
        crop_factor = 1.0
    
    # Clipping strategy
    clip_mode = st.radio(
        "✂️ Clipping Mode",
        [
            "Smart (Context-Based)",
            "Fixed (15-60 seconds)"
        ],
        help="Smart mode cuts based on topic completion"
    )
    
    st.markdown("---")
    st.header("📝 Subtitle Settings")
    
    enable_subs = st.checkbox(
        "Add Subtitles",
        value=False,
        help="Add styled captions to clips"
    )
    
    if enable_subs:
        sub_style = st.selectbox(
            "🎨 Subtitle Style",
            [
                "Bold Yellow (TikTok)",
                "White Shadow",
                "Black Outline",
                "Neon Glow",
                "Gradient Pop"
            ]
        )
    
    st.markdown("---")
    st.info(f"💡 Generating **{max_clips} clips** • **{aspect_ratio}** • **{video_quality}**")

# Main input
youtube_url = st.text_input(
    "🎥 YouTube URL:",
    placeholder="https://www.youtube.com/watch?v=..."
)

# Generate button
if st.button("🚀 Generate Clips", type="primary", use_container_width=True):
    
    if not youtube_url:
        st.error("❌ Please enter a YouTube URL")
    elif not api_key:
        st.error("❌ Please enter your Groq API key")
    else:
        try:
            client = Groq(api_key=api_key)
            
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # STEP 1: Download Video
                st.info("📥 Step 1/4: Downloading video in HD...")
                progress = st.progress(0)
                
                video_path = temp_path / "video.mp4"
                
                # Download in HIGHEST QUALITY available (up to 1080p)
                ydl_opts = {
                    'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best',
                    'outtmpl': str(video_path),
                    'quiet': True,
                    'merge_output_format': 'mp4'
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(youtube_url, download=True)
                    video_duration = info.get('duration', 0)
                    video_title = info.get('title', 'Video')
                
                st.success(f"✅ Downloaded: {video_title} (HD)")
                progress.progress(20)
                
                # STEP 2: Download Audio
                st.info("🎵 Step 2/4: Downloading audio...")
                
                audio_path = temp_path / "audio"
                
                ydl_opts_audio = {
                    'format': 'bestaudio',
                    'outtmpl': str(audio_path),
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                    }]
                }
                
                with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl:
                    ydl.extract_info(youtube_url, download=True)
                
                # Find audio file
                audio_file = None
                for ext in ['.mp3', '.m4a', '.webm']:
                    test = temp_path / f"audio{ext}"
                    if test.exists():
                        audio_file = test
                        break
                
                if not audio_file:
                    raise FileNotFoundError("Audio not found")
                
                progress.progress(35)
                
                # STEP 3: Transcribe
                st.info("🎤 Step 3/4: Transcribing audio...")
                
                model = whisper.load_model("tiny")
                result = model.transcribe(str(audio_file))
                
                transcript = ""
                for seg in result['segments']:
                    transcript += f"[{seg['start']:.1f}s-{seg['end']:.1f}s] {seg['text']}\n"
                
                st.success(f"✅ Transcribed {len(result['segments'])} segments")
                progress.progress(50)
                
                # STEP 4: AI Analysis
                st.info("🤖 Step 4/4: AI analyzing content...")
                
                if clip_mode == "Smart (Context-Based)":
                    duration_rule = """- Clip duration should match the COMPLETE topic discussion
- SHORT clips (10-30s) for jokes, reactions, quick tips
- MEDIUM clips (30-90s) for explanations, examples, stories
- LONG clips (90-180s) for full tutorials, deep dives
- DO NOT cut mid-sentence or mid-explanation
- Find natural topic boundaries and transitions"""
                else:
                    duration_rule = "- Each clip must be 15-60 seconds exactly"
                
                prompt = f"""You are an expert video editor. Analyze this transcript and find the TOP {max_clips} most viral-worthy clips.

Video: {video_title}
Duration: {video_duration}s

Transcript:
{transcript}

RULES:
{duration_rule}
- Each clip must be self-contained and make sense alone
- Look for: hooks, punchlines, insights, emotional moments
- Perfect for TikTok/Instagram/YouTube Shorts

Return EXACTLY {max_clips} clips in this JSON format (NO markdown, NO code blocks):
[
  {{
    "start_time": 10.5,
    "end_time": 45.2,
    "title": "Short descriptive title",
    "reason": "Why this clip is viral-worthy",
    "type": "educational/funny/inspiring/etc"
  }}
]"""

                response = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "You are a video editor. Respond ONLY with valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    model="llama-3.3-70b-versatile",
                    temperature=0.5,
                    max_tokens=2000
                )
                
                resp_text = response.choices[0].message.content.strip()
                
                # Clean JSON
                if "```json" in resp_text:
                    resp_text = resp_text.split("```json")[1].split("```")[0]
                elif "```" in resp_text:
                    resp_text = resp_text.split("```")[1].split("```")[0]
                
                clips_data = json.loads(resp_text.strip())
                
                st.success(f"✅ AI found {len(clips_data)} clips!")
                progress.progress(70)
                
                # STEP 5: Create Clips
                st.info(f"✂️ Creating {len(clips_data)} clips...")
                
                video = VideoFileClip(str(video_path))
                
                # Parse aspect ratio
                aspect_map = {
                    "Original (No Crop)": None,
                    "16:9 (YouTube)": (16, 9),
                    "9:16 (TikTok/Reels)": (9, 16),
                    "1:1 (Instagram)": (1, 1),
                    "4:5 (Instagram Portrait)": (4, 5)
                }
                target_aspect = aspect_map[aspect_ratio]
                
                final_clips = []
                
                for i, clip_data in enumerate(clips_data):
                    start = clip_data['start_time']
                    end = clip_data['end_time']
                    title = clip_data['title']
                    
                    if start < 0 or end > video_duration or start >= end:
                        continue
                    
                    st.write(f"📹 Clip {i+1}: {title} ({end-start:.1f}s)")
                    
                    # Cut clip
                    clip = video.subclip(start, end)
                    
                    # Apply aspect ratio
                    if target_aspect:
                        w, h = clip.size
                        target_w, target_h = target_aspect
                        target_ratio = target_w / target_h
                        current_ratio = w / h
                        
                        if abs(current_ratio - target_ratio) > 0.01:
                            if current_ratio > target_ratio:
                                # Crop width
                                new_w = int(h * target_ratio)
                                x1 = (w - new_w) // 2
                                clip = clip.crop(x1=x1, x2=x1+new_w)
                            else:
                                # Crop height
                                new_h = int(w / target_ratio)
                                y1 = (h - new_h) // 2
                                clip = clip.crop(y1=y1, y2=y1+new_h)
                            
                            st.write(f"  ✂️ Cropped to {target_w}:{target_h}")
                    
                    # Add subtitles
                    if enable_subs:
                        st.write(f"  📝 Adding subtitles...")
                        
                        try:
                            # Get relevant transcript segments
                            clip_subs = []
                            for seg in result['segments']:
                                if seg['start'] >= start and seg['start'] < end:
                                    rel_start = seg['start'] - start
                                    rel_end = min(seg['end'] - start, end - start)
                                    if rel_end > rel_start:
                                        clip_subs.append({
                                            'start': rel_start,
                                            'end': rel_end,
                                            'text': seg['text'].strip()
                                        })
                            
                            if clip_subs:
                                subtitle_clips = []
                                for sub in clip_subs[:20]:  # Limit to 20 subs per clip
                                    txt_clip = create_subtitle_clip(
                                        sub['text'],
                                        sub['end'] - sub['start'],
                                        clip.size,
                                        sub_style
                                    )
                                    if txt_clip:
                                        # Position at bottom
                                        y_pos = clip.h * 0.82
                                        txt_clip = txt_clip.set_start(sub['start']).set_position(('center', y_pos))
                                        subtitle_clips.append(txt_clip)
                                
                                if subtitle_clips:
                                    clip = CompositeVideoClip([clip] + subtitle_clips)
                                    st.write(f"  ✅ Added {len(subtitle_clips)} subtitle segments")
                        
                        except Exception as e:
                            st.warning(f"  ⚠️ Subtitle error: {str(e)}")
                    
                    # Save clip
                    clip_file = temp_path / f"clip_{i+1}.mp4"
                    
                    clip.write_videofile(
                        str(clip_file),
                        codec='libx264',
                        audio_codec='aac',
                        verbose=False,
                        logger=None
                    )
                    
                    # Clean up
                    clip.close()
                    del clip
                    
                    # Read to memory
                    with open(clip_file, 'rb') as f:
                        final_clips.append({
                            'data': f.read(),
                            'title': title,
                            'duration': end - start,
                            'start': start,
                            'end': end,
                            'reason': clip_data.get('reason', ''),
                            'type': clip_data.get('type', '')
                        })
                    
                    st.write(f"  ✅ Saved clip {i+1}")
                
                video.close()
                del video
                
                progress.progress(100)
                
                # Display results
                st.success(f"🎉 Created {len(final_clips)} clips!")
                st.balloons()
                
                for i, clip in enumerate(final_clips):
                    st.markdown("---")
                    
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.subheader(f"🎬 Clip {i+1}: {clip['title']}")
                        st.write(f"⏱️ **Duration:** {clip['duration']:.1f}s ({clip['start']:.1f}s - {clip['end']:.1f}s)")
                        if clip['reason']:
                            st.write(f"💡 **Why:** {clip['reason']}")
                        if clip['type']:
                            st.write(f"🏷️ **Type:** {clip['type']}")
                    
                    with col2:
                        st.download_button(
                            "⬇️ Download",
                            data=clip['data'],
                            file_name=f"clip_{i+1}_{clip['title'][:20]}.mp4",
                            mime="video/mp4",
                            key=f"dl_{i}",
                            use_container_width=True
                        )
                    
                    st.video(clip['data'])
        
        except json.JSONDecodeError as e:
            st.error(f"❌ AI response error: {str(e)}")
            st.code(resp_text)
        
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.code(traceback.format_exc())

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #888;'>
    <p><b>AI Video Clipper Pro</b> • Powered by Groq AI • Optimized for All Platforms</p>
    <p>🎯 Perfect for TikTok • Instagram • YouTube Shorts</p>
</div>
""", unsafe_allow_html=True)