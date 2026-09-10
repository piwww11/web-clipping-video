# 🎬 AI Video Clipper

An AI-powered video clipping tool that automatically analyzes long-form video transcripts and identifies relevant moments for short-form content.

This project combines **Whisper for speech-to-text** and **LLM-based analysis through Groq** to understand video context, identify potential clips, and generate short-form video segments.

---

## ✨ Features

- 🎥 YouTube video downloading
- 🧠 AI-powered transcript analysis
- ✂️ Automatic clip selection based on video context
- 📝 Automatic transcription using Whisper
- 🤖 LLM-powered content analysis using Groq
- 🎯 Context-based and time-based clipping
- 📱 Multiple aspect ratios for different platforms
  - 16:9
  - 9:16
  - 1:1
  - 4:5
  - Original
- 🔢 Customizable number of clips
- 💬 Stylized subtitles
- 🖥️ Simple Streamlit interface

---

## 🧠 How It Works

The application follows this workflow:

```text
YouTube URL
     ↓
Download Video
     ↓
Extract Audio
     ↓
Whisper Transcription
     ↓
Transcript Analysis
     ↓
LLM identifies potential clips
     ↓
Clip Generation
     ↓
Short-form Video Output
```

The AI analyzes the transcript and determines potential clip segments based on factors such as:

- Context
- Relevance
- Content type
- Potential hook
- Start and end timestamps

The selected timestamps are then processed automatically to generate the final clips.

---

## 🤖 AI & Prompting

One of the main components of this project is the use of an LLM to analyze video transcripts.

The transcript is sent to the model with a structured prompt requesting information such as:

- Clip start time
- Clip end time
- Suggested title
- Reason for selecting the segment
- Content type
- Potential hook

The model is instructed to return structured JSON data so the application can process the AI-generated results programmatically.

### AI Stack

| Component | Technology |
|---|---|
| Speech-to-Text | OpenAI Whisper |
| LLM | Llama 3.3 70B |
| LLM API | Groq |
| Prompt-based Analysis | Custom prompts |
| Video Processing | MoviePy |

---

## 🛠️ Tech Stack

- **Python**
- **Streamlit**
- **Whisper**
- **Groq API**
- **Llama 3.3 70B**
- **yt-dlp**
- **MoviePy**

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/piwww11/web-clipping-video.git
cd web-clipping-video
```

### 2. Install dependencies

Install the required Python packages:

```bash
pip install streamlit yt-dlp openai-whisper groq moviepy
```

> Additional dependencies may be required depending on your local environment and FFmpeg configuration.

### 3. Configure the Groq API Key

Create an environment variable for your Groq API key.

Example:

```env
GROQ_API_KEY=your_api_key_here
```

**Never commit API keys or other sensitive credentials to the repository.**

### 4. Run the application

```bash
streamlit run clipp.py
```

The Streamlit application will then be available locally in your browser.

---

## 🎯 Project Goals

This project was built to explore how AI can be used to simplify the process of transforming long-form content into short-form videos.

Instead of manually watching an entire video and searching for interesting moments, the system attempts to:

1. Understand the video's spoken content.
2. Analyze the context using an LLM.
3. Identify potentially valuable segments.
4. Convert those segments into short-form clips.

The project also serves as an exploration of **LLM prompting, structured AI outputs, and AI-assisted content creation workflows**.

---

## 🔍 What I Learned

Through this project, I explored:

- Working with LLM APIs
- Designing prompts for structured outputs
- Processing and analyzing transcripts
- Speech-to-text workflows
- Automated video processing
- Integrating multiple AI and media-processing tools
- Building an interactive AI application with Streamlit
- Turning AI-generated results into programmatically usable data

---

## ⚠️ Current Limitations

This project is currently a personal/experimental project and may have limitations when processing:

- Very long videos
- Videos with complex audio
- Poor-quality audio
- Different video formats
- Large numbers of clips

Processing time also depends on video length, transcription time, and available system resources.

---

## 📌 Future Improvements

Potential improvements include:

- [ ] Better clip quality scoring
- [ ] More advanced hook detection
- [ ] Automatic caption styling
- [ ] Support for additional video platforms
- [ ] Improved AI clip selection
- [ ] Automatic title and description generation
- [ ] Social-media-ready export presets
- [ ] Faster processing pipeline
- [ ] Web deployment

---

## 👨‍💻 Author

**Raffi Pratama**

Beginner developer interested in:

- Artificial Intelligence
- AI-assisted development
- Prompt Engineering
- Web Development
- Creative Technology

GitHub: https://github.com/piwww11

Portfolio: https://raffiporto.netlify.app
