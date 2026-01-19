# Image Generation

Create images using Gemini native or Imagen 4 models.

## Model Selection

| Model | Quality | Speed | Best For |
|-------|---------|-------|----------|
| gemini-2.5-flash-image | High | Fast | General use, iteration |
| gemini-3-pro-image | Ultra | Medium | Text rendering, complex prompts |
| imagen-4.0-generate-001 | High | Medium | Production assets |
| imagen-4.0-ultra-001 | Ultra | Slow | Marketing, final delivery |
| imagen-4.0-fast-001 | Good | Fast | Bulk generation |

## Basic Usage

```python
from mmio import MMIO

mm = MMIO()

# Simple generation
img = mm.imagine("sunset over mountains")
img.save("sunset.png")

# With parameters
img = mm.imagine(
    "product photo of headphones",
    ratio="4:3",
    size="2K",
    model="imagen-4.0-ultra-generate-001"
)
```

## Aspect Ratios

All models support: `1:1`, `2:3`, `3:2`, `3:4`, `4:3`, `4:5`, `5:4`, `9:16`, `16:9`, `21:9`

## Image Editing

Pass a reference image to edit or restyle:

```python
# Style transfer
img = mm.imagine(
    "convert to oil painting style",
    reference="photo.jpg"
)

# Object addition
img = mm.imagine(
    "add a hot air balloon in the sky",
    reference="landscape.jpg"
)
```

## Prompt Techniques

### Structure
```
[Subject] + [Action/State] + [Environment] + [Style] + [Technical]
```

### Example
```
"A red fox [subject] sitting alertly [action] in a snowy forest clearing [environment],
digital art style with soft lighting [style], 4K detailed [technical]"
```

### Text in Images
- Keep text under 25 characters
- Use `gemini-3-pro-image` for better text rendering
- Specify font style and position explicitly

```python
img = mm.imagine(
    'Poster with bold text "ADVENTURE" at top, mountain background',
    model="gemini-3-pro-image-preview",
    size="4K"
)
```

## Error Handling

```python
try:
    img = mm.imagine(prompt)
except Exception as e:
    if "safety" in str(e).lower():
        # Modify prompt
    elif "quota" in str(e).lower():
        # Wait and retry
```

## Costs

- Gemini Flash Image: ~$0.001/image
- Gemini Pro Image: ~$0.13/image
- Imagen 4 Standard: ~$0.02/image
- Imagen 4 Ultra: ~$0.04/image
