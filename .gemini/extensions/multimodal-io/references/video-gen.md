# Video Generation

Create 8-second videos with native audio using Veo 3.1.

## Models

| Model | Speed | Status | Notes |
|-------|-------|--------|-------|
| veo-3.1-generate-preview | Medium | Preview | Full features |
| veo-3.1-fast-generate-preview | Fast | Preview | Speed optimized |
| veo-3.0-generate-001 | Medium | Stable | Production ready |
| veo-3.0-fast-generate-001 | Fast | Stable | Production ready |

## Basic Usage

```python
from mmio import MMIO

mm = MMIO()

# Text to video
vid = mm.video("ocean waves crashing on rocks at sunset")
vid.save("ocean.mp4")

# With parameters
vid = mm.video(
    "drone footage over city skyline",
    resolution="1080p",
    ratio="16:9"
)
```

## Frame Control

Use start/end frames for controlled animation:

```python
# Animate from single image
vid = mm.video(
    "camera slowly pans right",
    start_frame="scene.jpg"
)

# Interpolate between two frames
vid = mm.video(
    "smooth transition between scenes",
    start_frame="frame1.jpg",
    end_frame="frame2.jpg"
)
```

## Configuration

| Option | Values | Default |
|--------|--------|---------|
| resolution | 720p, 1080p | 1080p |
| ratio | 16:9, 9:16, 1:1 | 16:9 |
| duration | 8 seconds | 8s (fixed) |

## Prompt Structure

```
[Scene description] + [Motion/Action] + [Camera movement] + [Mood/Style]
```

### Example
```
"A hummingbird hovering near flowers [scene],
wings beating rapidly [action],
slow-motion close-up tracking shot [camera],
warm natural lighting [mood]"
```

### Camera Keywords
- Movement: zoom in, zoom out, pan left/right, tilt up/down
- Style: tracking shot, aerial view, close-up, wide angle
- Speed: slow motion, time-lapse, real-time

## Timing Control

Explicit timing in prompts:
```python
vid = mm.video("""
0-2s: Close-up of coffee being poured
2-5s: Steam rising, camera pulls back
5-8s: Reveal full cafe scene
""")
```

## Generation Time

| Config | Expected Time |
|--------|---------------|
| 720p + fast model | 20-40s |
| 1080p + standard | 60-120s |
| With frames | +10-20s |

## Limitations

- Fixed 8 second duration
- 24fps output
- No custom audio upload
- 2-day retention for generated files
- Max 3 reference images

## Error Handling

```python
try:
    vid = mm.video(prompt)
except Exception as e:
    if "quota" in str(e).lower():
        # Free tier has zero quota for video gen
        print("Video generation requires billing")
```
