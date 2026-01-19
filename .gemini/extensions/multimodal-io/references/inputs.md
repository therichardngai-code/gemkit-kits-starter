# Input Processing

Handle text, images, audio, video, and documents in a unified way.

## Supported Formats

| Type | Extensions | Max Inline | Max File API |
|------|-----------|------------|--------------|
| Image | jpg, png, webp, gif, bmp | 20MB | 2GB |
| Audio | mp3, wav, flac, aac, ogg | 20MB | 2GB |
| Video | mp4, mov, avi, webm, mkv | 20MB | 2GB |
| Document | pdf, txt, html, md | 20MB | 2GB |

## Media Resolution

Control quality vs token consumption tradeoff:

```python
from mmio import MMIO, MediaResolution

mm = MMIO(default_resolution=MediaResolution.LOW)

# Or per-request
result = mm.process("large_image.jpg", "describe", resolution=MediaResolution.HIGH)
```

| Level | Tokens | Use Case |
|-------|--------|----------|
| LOW | ~100/sec video | Quick analysis, drafts |
| MEDIUM | ~300/sec video | Balanced (default) |
| HIGH | ~500/sec video | OCR, fine details |

## Input Methods

### File Path
```python
result = mm.process("photo.jpg", "describe this")
```

### Raw Bytes
```python
with open("photo.jpg", "rb") as f:
    result = mm.process(f.read(), "describe this")
```

### File-like Object
```python
from io import BytesIO
buffer = BytesIO(image_bytes)
result = mm.process(buffer, "describe this")
```

## Auto File API

Files >15MB automatically use Gemini File API:
- Uploads file to Google servers
- Returns URI for processing
- Handles async processing for video/audio

## Token Estimation

| Input Type | Tokens |
|------------|--------|
| Image (standard) | ~1,260 per image |
| Audio | ~32 per second |
| Video (1fps) | ~300 per second |
| PDF | ~varies by content |

## Best Practices

1. **Use LOW resolution** for initial analysis, switch to HIGH for detail work
2. **Batch similar files** to reduce API overhead
3. **Chunk long audio/video** (>15min) for complete transcription
4. **Pre-compress** large files before upload when possible
