# Streaming & Real-time

Handle streaming responses and real-time multimodal interactions.

## Streaming Text Output

For long-form responses, stream tokens as they generate:

```python
from google import genai
from google.genai import types

client = genai.Client()

# Stream text response
for chunk in client.models.generate_content_stream(
    model="gemini-3-flash",
    contents="Write a detailed analysis of this image",
):
    print(chunk.text, end="", flush=True)
```

## Async Processing

Handle long operations without blocking:

```python
import asyncio
from mmio import MMIO

async def process_batch(files):
    mm = MMIO()
    tasks = []

    for f in files:
        task = asyncio.to_thread(mm.process, f, "analyze")
        tasks.append(task)

    results = await asyncio.gather(*tasks)
    return results
```

## Video Generation Polling

Video generation is async by nature:

```python
from mmio import MMIO
import time

mm = MMIO()

# Start generation (returns when complete)
vid = mm.video("ocean sunset")

# For progress tracking, use raw API:
from google import genai

client = genai.Client()
operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    prompt="ocean waves"
)

while not operation.done:
    print(f"Status: {operation.metadata}")
    time.sleep(10)
    operation = client.operations.get(operation)

print("Complete!")
```

## Live API (Preview)

Real-time bidirectional streaming for voice/video:

```python
from google import genai

client = genai.Client()

# Start live session
session = client.live.connect(model="gemini-3-flash")

# Send audio chunk
session.send_audio(audio_bytes)

# Receive response
for response in session.receive():
    if response.audio:
        play_audio(response.audio)
    if response.text:
        print(response.text)

session.close()
```

## Chunking Large Files

For transcription of long audio/video (>15 min):

```python
from pathlib import Path
import subprocess

def chunk_audio(filepath, chunk_minutes=15):
    """Split audio into chunks using ffmpeg."""
    output_pattern = f"{Path(filepath).stem}_chunk_%03d.mp3"

    subprocess.run([
        "ffmpeg", "-i", filepath,
        "-f", "segment",
        "-segment_time", str(chunk_minutes * 60),
        "-c", "copy",
        output_pattern
    ])

    return sorted(Path(".").glob(f"{Path(filepath).stem}_chunk_*.mp3"))

# Process chunks
mm = MMIO()
chunks = chunk_audio("long_meeting.mp3")

transcripts = []
for chunk in chunks:
    result = mm.transcribe(chunk, timestamps=True)
    transcripts.append(result.text)

full_transcript = "\n".join(transcripts)
```

## Rate Limiting

Handle quota limits gracefully:

```python
import time
from functools import wraps

def with_retry(max_retries=3, base_delay=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if "429" in str(e) or "quota" in str(e).lower():
                        delay = base_delay * (2 ** attempt)
                        time.sleep(delay)
                    else:
                        raise
            raise Exception("Max retries exceeded")
        return wrapper
    return decorator

@with_retry()
def safe_process(mm, file, prompt):
    return mm.process(file, prompt)
```
