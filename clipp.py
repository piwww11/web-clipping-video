import streamlit as st
import yt_dlp
import whisper
from groq import Groq
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.tools.subtitles import SubtitlesClip
from moviepy.editor import TextClip, CompositeVideoClip
import json
import os
import tempfile
import traceback
import time
from pathlib import Path

# Page config
st.set_page_config(
    page_title="AI Video Clipper Pro",
    page_icon="✂️",
    layout="wide"
)

# Subtitle styling function
def create_styled_subtitle(txt, style):
    """Create styled subtitle based on selected style"""
    styles = {
        "Bold Yellow (TikTok Style)": {
            'fontsize': 50,
            'font': 'Arial-Bold',
            'color': 'yellow',
            'stroke_color': 'black',
            'stroke_width': 3,
            'method': 'caption',
            'align': 'center'
        },
        "White Shadow (Clean)": {
            'fontsize': 45,
            'font': 'Arial-Bold',
            'color': 'white',
            'stroke_color': 'black',
            'stroke_width': 2,
            'method': 'caption',
            'align': 'center'
        },
        "Black Outline (Strong)": {
            'fontsize': 48,
            'font': 'Impact',
            'color': 'white',
            'stroke_color': 'black',
            'stroke_width': 4,
            'method': 'caption',
            'align': 'center'
        },
        "Neon Glow (Futuristic)": {
            'fontsize': 46,
            'font': 'Arial-Bold',
            'color': '#00FF00',
            'stroke_color': '#00FFFF',
            'stroke_width': 2,
            'method': 'caption',
            'align': 'center'
        },
        "Gradient Pop (Colorful)": {
            'fontsize': 52,
            'font': 'Arial-Black',
            'color': '#FF1493',
            'stroke_color': '#FFD700',
            'stroke_width': 3,
            'method': 'caption',
            'align': 'center'
        }
    }
    
    style_config = styles.get(style, styles["Bold Yellow (TikTok Style)"])
    
    return TextClip(
        txt,
        fontsize=style_config['fontsize'],
        font=style_config['font'],
        color=style_config['color'],
        stroke_color=style_config['stroke_color'],
        stroke_width=style_config['stroke_width'],
        method=style_config['method'],
        align=style_config['align'],
        size=(None, None)
    )

# Title and description
st.title("✂️ AI Video Clipper Pro")
st.markdown("""
**🚀 Advanced AI-powered video clipper with smart context detection**

Upload a YouTube URL → AI analyzes content → Creates viral-ready clips with custom aspect ratios!
""")

# Feature highlights
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("🎯 Max Clips", "1-10")
with col2:
    st.metric("📐 Aspect Ratios", "5 Options")
with col3:
    st.metric("🤖 AI Strategy", "Context-Based")
with col4:
    st.metric("📝 Subtitles", "5 Styles")

# Sidebar for API key
with st.sidebar:
    st.header("🔑 Configuration")
    api_key = st.text_input(
        "Groq API Key",
        type="password",
        help="Get your free API key from https://console.groq.com/keys"
    )
    
    st.markdown("---")
    st.header("🎬 Clip Settings")
    
    # Aspect ratio selector
    aspect_ratio = st.selectbox(
        "📐 Aspect Ratio",
        options=[
            "16:9 (YouTube/Landscape)",
            "9:16 (TikTok/Instagram Reels)",
            "1:1 (Instagram Feed)",
            "4:5 (Instagram Portrait)",
            "Original (No Crop)"
        ],
        index=0
    )
    
    # Max clips selector
    max_clips = st.slider(
        "🎯 Maximum Clips to Generate",
        min_value=1,
        max_value=10,
        value=3,
        help="More clips = longer processing time"
    )
    
    # Clipping strategy
    clip_strategy = st.radio(
        "✂️ Clipping Strategy",
        options=[
            "Context-Based (Smart)",
            "Time-Based (15-60s)"
        ],
        help="Context-Based: AI determines clip length based on topic completeness"
    )
    
    # Subtitle options
    add_subtitles = st.checkbox(
        "📝 Add Stylized Subtitles",
        value=False,
        help="Adds animated captions to clips (like viral TikTok videos)"
    )
    
    if add_subtitles:
        subtitle_style = st.selectbox(
            "🎨 Subtitle Style",
            options=[
                "Bold Yellow (TikTok Style)",
                "White Shadow (Clean)",
                "Black Outline (Strong)",
                "Neon Glow (Futuristic)",
                "Gradient Pop (Colorful)"
            ]
        )
    else:
        subtitle_style = None
    
    st.markdown("---")
    st.markdown("### 📋 How it works:")
    st.markdown("""
    1. Downloads YouTube video
    2. Transcribes audio with AI
    3. Analyzes content with Groq (Super Fast!)
    4. Clips based on your settings
    5. Applies aspect ratio & effects
    """)
    
    st.markdown("---")
    st.markdown("### ⚠️ Limitations:")
    st.markdown("""
    - Videos under 10 minutes recommended
    - Processing takes 2-5 minutes
    - More clips = longer processing
    """)
    
    st.markdown("---")
    st.info("💡 **Context-Based clipping** creates clips based on topic boundaries, not fixed time!")

# Main interface
youtube_url = st.text_input(
    "🎥 Enter YouTube URL:",
    placeholder="https://www.youtube.com/watch?v=..."
)

if st.button("🚀 Generate Clips", type="primary"):
    if not youtube_url:
        st.error("Please enter a YouTube URL")
    elif not api_key:
        st.error("Please enter your Groq API Key in the sidebar")
    else:
        try:
            # Initialize Groq client
            client = Groq(api_key=api_key)
            
            # Create temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Step 1: Download video
                st.info("📥 Step 1/4: Downloading video...")
                progress_bar = st.progress(0)
                
                video_path = temp_path / "video.mp4"
                
                # Download video
                ydl_opts_video = {
                    'format': 'best[height<=720]',
                    'outtmpl': str(video_path),
                    'quiet': True,
                    'no_warnings': True,
                }
                
                with yt_dlp.YoutubeDL(ydl_opts_video) as ydl:
                    info = ydl.extract_info(youtube_url, download=True)
                    video_duration = info.get('duration', 0)
                    video_title = info.get('title', 'Unknown')
                
                if video_duration > 600:
                    st.warning(f"⚠️ Video is {video_duration//60} minutes long. Processing may be slow.")
                
                progress_bar.progress(25)
                
                # Download audio
                st.info("🎵 Downloading audio for transcription...")
                
                audio_base = temp_path / "audio"
                
                ydl_opts_audio = {
                    'format': 'bestaudio/best',
                    'outtmpl': str(audio_base),
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                    }],
                }
                
                with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl:
                    ydl.extract_info(youtube_url, download=True)
                
                # Find audio file
                audio_file = None
                for ext in ['.mp3', '.m4a', '.webm', '.opus']:
                    test_path = temp_path / f"audio{ext}"
                    if test_path.exists():
                        audio_file = test_path
                        break
                
                if not audio_file:
                    raise FileNotFoundError("Audio file not created")
                
                st.success(f"✅ Audio downloaded: {audio_file.name}")
                progress_bar.progress(40)
                
                # Step 2: Transcribe
                st.info("🎤 Step 2/4: Transcribing audio...")
                
                model = whisper.load_model("tiny")
                result = model.transcribe(str(audio_file))
                
                full_transcript = ""
                for segment in result['segments']:
                    full_transcript += f"[{segment['start']:.1f}s - {segment['end']:.1f}s] {segment['text']}\n"
                
                st.success(f"✅ Transcribed {len(result['segments'])} segments!")
                progress_bar.progress(60)
                
                # Step 3: AI Analysis
                st.info("🤖 Step 3/4: Analyzing content with Groq AI...")
                
                # Build prompt based on clipping strategy
                if clip_strategy == "Context-Based (Smart)":
                    duration_instruction = """- Clip length should match the COMPLETE discussion of a topic (can be 10 seconds to 2 minutes)
- DON'T cut in the middle of an explanation or story
- Each clip should have a clear BEGINNING (hook), MIDDLE (content), and END (conclusion/punchline)
- For educational content: capture the full concept explanation
- For stories: capture the complete narrative arc
- Short clips (10-30s) for quick jokes/reactions
- Medium clips (30-90s) for explanations/examples
- Long clips (90-120s) for complete stories/tutorials"""
                else:
                    duration_instruction = "- Each clip must be 15-60 seconds"
                
                prompt = f"""You are an expert video editor analyzing a transcript to find the most engaging, viral-worthy clips.

Video Title: {video_title}
Duration: {video_duration} seconds

Transcript with timestamps:
{full_transcript}

Task: Identify the TOP {max_clips} BEST clips that are:
- Funny, surprising, emotionally engaging, or highly educational
- Self-contained (make sense on their own with complete context)
- Have a clear hook or value proposition
- Would perform well on social media (TikTok, Instagram Reels, YouTube Shorts)
- Based on TOPIC BOUNDARIES, not arbitrary time cuts

CLIPPING RULES:
{duration_instruction}
- Look for natural topic transitions (speaker changes subject, pauses, conclusion phrases)
- Prioritize clips where the speaker completes a full thought/example/story
- Avoid cutting mid-sentence or mid-explanation

Return ONLY a valid JSON array with this exact format:
[
  {{
    "start_time": 10.5,
    "end_time": 95.3,
    "title": "How Inflation Affects Your Savings - Real Example",
    "reason": "Complete explanation with concrete example, perfect for educational short",
    "content_type": "educational",
    "hook": "Speaker starts with relatable question about money"
  }}
]

IMPORTANT:
- Return EXACTLY {max_clips} clips (no more, no less)
- Use exact timestamp numbers from the transcript
- Ensure timestamps capture COMPLETE thoughts/topics
- Return ONLY the JSON array, no markdown, no code blocks"""

                chat_completion = client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a professional video editor who understands content context and topic boundaries. You respond ONLY with valid JSON arrays."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    model="llama-3.3-70b-versatile",
                    temperature=0.5,
                    max_tokens=2000,
                )
                
                response_text = chat_completion.choices[0].message.content.strip()
                
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0].strip()
                
                clips = json.loads(response_text)
                
                progress_bar.progress(75)
                
                # Step 4: Create clips
                st.info(f"✂️ Step 4/4: Creating {len(clips)} clips with {aspect_ratio}...")
                
                # Parse aspect ratio
                aspect_ratios = {
                    "16:9 (YouTube/Landscape)": (16, 9),
                    "9:16 (TikTok/Instagram Reels)": (9, 16),
                    "1:1 (Instagram Feed)": (1, 1),
                    "4:5 (Instagram Portrait)": (4, 5),
                    "Original (No Crop)": None
                }
                target_ratio = aspect_ratios[aspect_ratio]
                
                video = VideoFileClip(str(video_path))
                
                clip_files = []
                for i, clip_info in enumerate(clips):
                    start = clip_info['start_time']
                    end = clip_info['end_time']
                    title = clip_info['title']
                    
                    if start < 0 or end > video_duration or start >= end:
                        st.warning(f"⚠️ Skipping invalid clip: {title}")
                        continue
                    
                    duration = end - start
                    st.write(f"Creating clip {i+1}/{len(clips)}: {title} ({duration:.1f}s)...")
                    
                    clip = video.subclip(start, end)
                    
                    # Apply aspect ratio cropping
                    if target_ratio:
                        target_w, target_h = target_ratio
                        target_aspect = target_w / target_h
                        
                        w, h = clip.size
                        current_aspect = w / h
                        
                        if abs(current_aspect - target_aspect) > 0.01:  # Need cropping
                            if current_aspect > target_aspect:
                                # Video is wider, crop width
                                new_w = int(h * target_aspect)
                                x_center = w // 2
                                x1 = x_center - new_w // 2
                                clip = clip.crop(x1=x1, x2=x1 + new_w)
                            else:
                                # Video is taller, crop height
                                new_h = int(w / target_aspect)
                                y_center = h // 2
                                y1 = y_center - new_h // 2
                                clip = clip.crop(y1=y1, y2=y1 + new_h)
                            
                            st.write(f"  ✂️ Cropped to {target_w}:{target_h}")
                    
                    clip_filename = temp_path / f"clip_{i+1}.mp4"
                    
                    # Add subtitles if enabled
                    if add_subtitles and subtitle_style:
                        st.write(f"  📝 Adding subtitles ({subtitle_style})...")
                        
                        # Get transcript for this clip timeframe
                        clip_transcript = []
                        for segment in result['segments']:
                            seg_start = segment['start']
                            seg_end = segment['end']
                            
                            # Check if segment overlaps with clip
                            if (seg_start >= start and seg_start < end) or (seg_end > start and seg_end <= end):
                                # Adjust times relative to clip start
                                relative_start = max(0, seg_start - start)
                                relative_end = min(duration, seg_end - start)
                                
                                if relative_end > relative_start:
                                    clip_transcript.append({
                                        'start': relative_start,
                                        'end': relative_end,
                                        'text': segment['text'].strip()
                                    })
                        
                        # Create subtitle clips
                        def make_subtitle(txt):
                            return create_styled_subtitle(txt, subtitle_style)
                        
                        # Generate subtitle timings
                        subtitle_timings = [(sub['start'], sub['end'], sub['text']) for sub in clip_transcript]
                        
                        if subtitle_timings:
                            try:
                                subtitles = SubtitlesClip(subtitle_timings, make_subtitle)
                                
                                # Position subtitles at bottom (10% from bottom for 9:16, 20% for others)
                                if "9:16" in aspect_ratio:
                                    subtitle_position = ('center', clip.h * 0.80)
                                else:
                                    subtitle_position = ('center', clip.h * 0.85)
                                
                                subtitles = subtitles.set_position(subtitle_position)
                                
                                # Composite video with subtitles
                                clip = CompositeVideoClip([clip, subtitles])
                                
                                st.write(f"  ✅ Added {len(clip_transcript)} subtitle segments")
                            except Exception as e:
                                st.warning(f"  ⚠️ Could not add subtitles: {str(e)}")
                    
                    clip.write_videofile(
                        str(clip_filename),
                        codec='libx264',
                        audio_codec='aac',
                        temp_audiofile=str(temp_path / f'temp_audio_{i}.m4a'),
                        remove_temp=True,
                        verbose=False,
                        logger=None
                    )
                    
                    # Close clip properly
                    clip.reader.close()
                    if clip.audio:
                        clip.audio.reader.close_proc()
                    clip.close()
                    del clip
                    
                    clip_files.append({
                        'path': clip_filename,
                        'title': title,
                        'start': start,
                        'end': end,
                        'duration': duration,
                        'reason': clip_info.get('reason', ''),
                        'content_type': clip_info.get('content_type', 'general'),
                        'hook': clip_info.get('hook', '')
                    })
                
                # Close video properly
                video.reader.close()
                if video.audio:
                    video.audio.reader.close_proc()
                video.close()
                del video
                
                time.sleep(0.5)  # Give Windows time to release file handles
                
                progress_bar.progress(90)
                
                # Read clips into memory (Windows workaround)
                st.info("📦 Preparing clips for download...")
                clips_data = []
                for clip in clip_files:
                    with open(clip['path'], 'rb') as f:
                        clips_data.append({
                            'data': f.read(),
                            'title': clip['title'],
                            'start': clip['start'],
                            'end': clip['end'],
                            'duration': clip['duration'],
                            'reason': clip['reason']
                        })
                
                progress_bar.progress(100)
                
                # Display results
                st.success(f"✅ Created {len(clips_data)} clips!")
                
                for i, clip in enumerate(clips_data):
                    st.markdown("---")
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.subheader(f"🎬 Clip {i+1}: {clip['title']}")
                        st.write(f"**Duration:** {clip['duration']:.1f}s ({clip['start']:.1f}s - {clip['end']:.1f}s)")
                        if clip['reason']:
                            st.write(f"**Why this clip:** {clip['reason']}")
                        if clip.get('content_type'):
                            st.write(f"**Type:** {clip['content_type'].title()}")
                        if clip.get('hook'):
                            st.write(f"**Hook:** {clip['hook']}")
                    
                    with col2:
                        st.download_button(
                            label="⬇️ Download Clip",
                            data=clip['data'],
                            file_name=f"clip_{i+1}_{clip['title'][:30]}.mp4",
                            mime="video/mp4",
                            key=f"download_{i}"
                        )
                    
                    st.video(clip['data'])
                
                st.balloons()
                
        except json.JSONDecodeError as e:
            st.error(f"❌ Failed to parse AI response: {str(e)}")
            st.code(response_text)
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.code(traceback.format_exc())

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p><strong>AI Video Clipper Pro</strong> • Powered by Groq AI • Windows Optimized</p>
    <p>💡 Features: Context-Based Clipping • Multi-Format Export • Stylized Subtitles</p>
    <p>🎯 Perfect for: TikTok • Instagram Reels • YouTube Shorts • All Platforms</p>
</div>
""", unsafe_allow_html=True)