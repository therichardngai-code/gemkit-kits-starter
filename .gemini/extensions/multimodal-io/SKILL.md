---
name: multimodal-io
description: Unified multimodal I/O with Gemini 3. Handle text/image/audio/video inputs, generate images (Imagen/Gemini), videos (Veo). Supports media resolution control, thinking levels, streaming.
license: MIT
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
---

# Multimodal I/O

Unified interface for processing and generating multimodal content via Gemini 3 API.

## Setup

```bash
pip install google-genai pillow
```

### API Key Configuration

The script auto-loads `GEMINI_API_KEY` from `.env` files in priority order:

1. **Skill dir**: `.gemini/extensions/multimodal-io/.env` (highest)
2. **Project root**: `.env` (searches up to git root)
3. **User home**: `~/.gemini/.env`, `~/.gemini.env`, `~/.env`

Environment variables set directly (`export GEMINI_API_KEY=...`) take precedence over all `.env` files.

## CLI Usage

```bash
# Process any media
python scripts/mmio.py process <file> --prompt "describe this"

# Generate image
python scripts/mmio.py imagine "sunset over mountains" --ratio 16:9

# Generate video
python scripts/mmio.py video "waves on beach" --duration 8

# Transcribe audio/video
python scripts/mmio.py transcribe <file> --timestamps

# Convert document to markdown
python scripts/mmio.py convert <pdf|docx> --output result.md
```

## Python API

```python
from mmio import MMIO

mm = MMIO()

# Analyze any media
result = mm.process("photo.jpg", "what objects are visible?")

# Generate image
img = mm.imagine("cyberpunk city", ratio="16:9", size="2K")

# Generate video
vid = mm.video("flying through clouds", resolution="1080p")

# Transcribe with timestamps
text = mm.transcribe("meeting.mp3", timestamps=True)
```

## Models

| Task | Default | Alternatives |
|------|---------|--------------|
| Analysis | gemini-3-flash-preview | gemini-3-pro-preview |
| Image Gen | gemini-2.5-flash-image | imagen-4.0-*, gemini-3-pro-preview-image |
| Video Gen | veo-3.1-generate-preview | veo-3.1-fast-* |
| Transcription | gemini-3-flash-preview | gemini-3-pro-preview |

## Key Features

- **Media Resolution**: Control quality/token tradeoff (`low`/`medium`/`high`)
- **Thinking Levels**: Adjust reasoning depth (`minimal`/`low`/`high`)
- **Streaming**: Real-time output for long operations
- **Auto-chunking**: Handles large files automatically

## References

| Topic | File |
|-------|------|
| Input Processing | `references/inputs.md` |
| Image Generation | `references/image-gen.md` |
| Video Generation | `references/video-gen.md` |
| Streaming & Live | `references/streaming.md` |

## Limits

- Inline: 20MB | File API: 2GB
- Audio: 9.5h max | Video: 1h max
- Image gen: 4 per request | Video: 8s duration
