#!/usr/bin/env python3
"""
Unified Multimodal I/O interface for Gemini 3 API.

Provides clean OOP interface for:
- Processing any media (images, audio, video, documents)
- Generating images via Imagen 4 or Gemini native
- Generating videos via Veo 3.1
- Transcribing audio/video with timestamps
- Converting documents to structured formats
"""

import argparse
import base64
import mimetypes
import os
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional, Union, List, BinaryIO

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Missing: pip install google-genai")
    sys.exit(1)


# Error messages for billing/quota issues
FREE_TIER_MSG = """
[FREE TIER LIMITATION] Image/Video generation unavailable on free tier.

Free tier has zero quota (limit: 0) for:
- Imagen models (imagen-4.0-*)
- Veo models (veo-*)
- Gemini image models (gemini-*-image)

Solutions:
1. Enable billing: https://aistudio.google.com/apikey
2. Use Google Cloud $300 credits: https://cloud.google.com/free

STOP: Don't retry - free tier will always fail for generation.
""".strip()

BILLING_MSG = """
[BILLING REQUIRED] This operation requires a paid account.

Enable billing at: https://aistudio.google.com/apikey
""".strip()


class BillingError(Exception):
    """Raised when operation requires billing."""
    pass


class FreeTierQuotaError(Exception):
    """Raised when free tier has zero quota for operation."""
    pass


def _is_billing_error(error: Exception) -> bool:
    """Check if error indicates billing is required."""
    msg = str(error).lower()
    indicators = ['billing', 'billed users', 'payment', 'not authorized', 'permission denied']
    return any(ind in msg for ind in indicators)


def _is_free_tier_quota_error(error: Exception) -> bool:
    """Check if error indicates free tier has zero quota."""
    msg = str(error)
    return 'RESOURCE_EXHAUSTED' in msg and ('limit: 0' in msg or 'free_tier' in msg.lower())


def _wrap_generation_error(error: Exception, operation: str) -> Exception:
    """Convert API errors to descriptive exceptions."""
    if _is_free_tier_quota_error(error):
        return FreeTierQuotaError(f"{operation} failed.\n\n{FREE_TIER_MSG}")
    if _is_billing_error(error):
        return BillingError(f"{operation} failed.\n\n{BILLING_MSG}")
    return error


def _load_env_files() -> dict:
    """
    Load environment variables from .env files with fallback hierarchy.

    Search order (first found wins for each variable):
    1. Skill directory: .gemini/extensions/multimodal-io/.env
    2. Project root: .env (cwd and parents up to git root)
    3. User home: ~/.env or ~/gemini.env

    Returns dict of loaded variables (also sets os.environ).
    """
    loaded = {}
    script_dir = Path(__file__).parent.parent  # multimodal-io/

    # Define search paths in priority order (later overwrites earlier)
    env_paths = []

    # 1. User home directory
    home = Path.home()
    env_paths.extend([
        home / '.gemini' / '.env',  # ~/.gemini/.env (Gemini CLI config dir)
        home / '.gemini.env',       # ~/.gemini.env
        home / 'gemini.env',        # ~/gemini.env
        home / '.env',              # ~/.env
    ])

    # 2. Project root (search upward for .git or .env)
    cwd = Path.cwd()
    for parent in [cwd] + list(cwd.parents):
        env_paths.append(parent / '.env')
        if (parent / '.git').exists():
            break  # Stop at git root

    # 3. Skill directory (highest priority)
    env_paths.append(script_dir / '.env')

    # Load in order (later files override earlier)
    for env_path in env_paths:
        if env_path.exists() and env_path.is_file():
            try:
                loaded.update(_parse_env_file(env_path))
            except Exception:
                pass  # Skip unparseable files

    # Apply to environment
    for key, value in loaded.items():
        if key not in os.environ:  # Don't override existing env vars
            os.environ[key] = value

    return loaded


def _parse_env_file(filepath: Path) -> dict:
    """Parse a .env file into a dict. Handles quotes, comments, encoding issues."""
    result = {}

    try:
        content = filepath.read_bytes()
        # Remove BOM if present
        if content.startswith(b'\xef\xbb\xbf'):
            content = content[3:]
        # Decode and strip null characters
        content = content.decode('utf-8', errors='ignore')
        content = content.replace('\x00', '')
    except Exception:
        return result

    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        if '=' not in line:
            continue

        key, _, value = line.partition('=')
        key = key.strip()
        value = value.strip()

        # Remove surrounding quotes
        if len(value) >= 2:
            if (value[0] == '"' and value[-1] == '"') or \
               (value[0] == "'" and value[-1] == "'"):
                value = value[1:-1]

        # Remove inline comments (but not inside quotes)
        if '#' in value and not value.startswith(('"', "'")):
            value = value.split('#')[0].strip()

        # Skip if key/value has invalid characters
        if '\x00' in key or '\x00' in value:
            continue

        if key:
            result[key] = value

    return result


# Auto-load .env files on module import
_load_env_files()


class MediaResolution(Enum):
    """Control quality vs token tradeoff for media inputs."""
    LOW = "media_resolution_low"
    MEDIUM = "media_resolution_medium"
    HIGH = "media_resolution_high"


class ThinkingLevel(Enum):
    """Control reasoning depth for complex tasks."""
    MINIMAL = "minimal"
    LOW = "low"
    HIGH = "high"


@dataclass
class GeneratedMedia:
    """Container for generated media output."""
    data: bytes
    path: Optional[str] = None
    mime_type: str = "application/octet-stream"
    metadata: dict = field(default_factory=dict)

    def save(self, filepath: str) -> str:
        """Save media to file and return path."""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'wb') as f:
            f.write(self.data)
        self.path = filepath
        return filepath


@dataclass
class ProcessResult:
    """Container for processing results."""
    text: Optional[str] = None
    media: Optional[GeneratedMedia] = None
    tokens_used: int = 0
    duration_ms: int = 0
    model: str = ""


class MMIO:
    """
    Unified Multimodal I/O interface.

    Examples:
        mm = MMIO()

        # Analyze image
        result = mm.process("photo.jpg", "describe the scene")

        # Generate image
        img = mm.imagine("mountain at sunset", ratio="16:9")
        img.save("output.png")

        # Generate video
        vid = mm.video("ocean waves", resolution="1080p")
        vid.save("output.mp4")
    """

    # Model defaults by task
    MODELS = {
        'analyze': 'gemini-3-flash-preview',
        'transcribe': 'gemini-3-flash-preview',
        'imagine': 'gemini-2.5-flash-image',
        'video': 'veo-3.1-generate-preview',
    }

    # MIME type mappings
    MIME_MAP = {
        '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
        '.webp': 'image/webp', '.gif': 'image/gif', '.bmp': 'image/bmp',
        '.mp3': 'audio/mp3', '.wav': 'audio/wav', '.flac': 'audio/flac',
        '.aac': 'audio/aac', '.ogg': 'audio/ogg', '.m4a': 'audio/mp4',
        '.mp4': 'video/mp4', '.mov': 'video/quicktime', '.avi': 'video/x-msvideo',
        '.webm': 'video/webm', '.mkv': 'video/x-matroska',
        '.pdf': 'application/pdf', '.txt': 'text/plain',
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_resolution: MediaResolution = MediaResolution.MEDIUM,
        default_thinking: ThinkingLevel = ThinkingLevel.LOW,
    ):
        """
        Initialize MMIO client.

        Args:
            api_key: Gemini API key (defaults to GEMINI_API_KEY env var)
            default_resolution: Default media resolution for inputs
            default_thinking: Default thinking level for complex tasks
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY required")

        self.client = genai.Client(api_key=self.api_key)
        self.default_resolution = default_resolution
        self.default_thinking = default_thinking
        self._output_dir = Path.cwd() / "generated"

    def _get_mime(self, filepath: Union[str, Path]) -> str:
        """Determine MIME type from file extension."""
        ext = Path(filepath).suffix.lower()
        return self.MIME_MAP.get(ext, 'application/octet-stream')

    def _is_youtube_url(self, source: str) -> bool:
        """Check if source is a YouTube URL."""
        if not isinstance(source, str):
            return False
        yt_patterns = ['youtube.com/watch', 'youtu.be/', 'youtube.com/shorts']
        return any(p in source for p in yt_patterns)

    def _load_media(self, source: Union[str, Path, bytes, BinaryIO]) -> tuple:
        """Load media from various sources. Returns (data, mime_type) or (url, 'youtube')."""
        if isinstance(source, bytes):
            return source, 'application/octet-stream'

        if hasattr(source, 'read'):
            return source.read(), 'application/octet-stream'

        # Check for YouTube URL first
        if isinstance(source, str) and self._is_youtube_url(source):
            return source, 'youtube'

        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {source}")

        return path.read_bytes(), self._get_mime(path)

    def _should_use_file_api(self, data: bytes) -> bool:
        """Determine if File API should be used based on size."""
        return len(data) > 15 * 1024 * 1024  # 15MB threshold

    def _upload_file(self, data: bytes, mime_type: str, name: str = "upload") -> any:
        """Upload file to Gemini File API."""
        import tempfile

        # Get extension from mime type for temp file
        ext_map = {v: k for k, v in self.MIME_MAP.items()}
        ext = ext_map.get(mime_type, '.bin')

        # Use proper temp directory (cross-platform)
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(data)
            temp_path = Path(tmp.name)

        try:
            # Pass mime_type to File API
            uploaded = self.client.files.upload(
                file=str(temp_path),
                config=types.UploadFileConfig(mime_type=mime_type)
            )
            # Wait for processing if needed
            while uploaded.state.name == 'PROCESSING':
                time.sleep(1)
                uploaded = self.client.files.get(name=uploaded.name)
            return uploaded
        finally:
            temp_path.unlink(missing_ok=True)

    def process(
        self,
        source: Union[str, Path, bytes],
        prompt: str,
        model: Optional[str] = None,
        resolution: Optional[MediaResolution] = None,
        thinking: Optional[ThinkingLevel] = None,
        output_json: bool = False,
    ) -> ProcessResult:
        """
        Process any media input with a text prompt.

        Args:
            source: File path, bytes, file-like object, or YouTube URL
            prompt: Instruction for processing
            model: Override default model
            resolution: Media resolution (quality vs tokens)
            thinking: Reasoning depth level
            output_json: Request JSON-formatted output

        Returns:
            ProcessResult with text response
        """
        start = time.time()
        model = model or self.MODELS['analyze']
        resolution = resolution or self.default_resolution

        # Load media
        data, mime_type = self._load_media(source)

        # Build content parts
        if mime_type == 'youtube':
            # YouTube URL - use directly with from_uri
            media_part = types.Part.from_uri(file_uri=data, mime_type='video/mp4')
        elif self._should_use_file_api(data):
            uploaded = self._upload_file(data, mime_type)
            media_part = types.Part.from_uri(file_uri=uploaded.uri, mime_type=mime_type)
        else:
            media_part = types.Part.from_bytes(data=data, mime_type=mime_type)

        # Build config
        config_args = {}
        if output_json:
            config_args['response_mime_type'] = 'application/json'

        config = types.GenerateContentConfig(**config_args) if config_args else None

        # Generate
        response = self.client.models.generate_content(
            model=model,
            contents=[media_part, prompt],
            config=config,
        )

        return ProcessResult(
            text=response.text if hasattr(response, 'text') else None,
            duration_ms=int((time.time() - start) * 1000),
            model=model,
        )

    def imagine(
        self,
        prompt: str,
        model: Optional[str] = None,
        ratio: str = "1:1",
        size: str = "1K",
        count: int = 1,
        reference: Optional[Union[str, Path, bytes]] = None,
    ) -> GeneratedMedia:
        """
        Generate image from text prompt.

        Args:
            prompt: Description of desired image
            model: Model to use (default: gemini-2.5-flash-image)
            ratio: Aspect ratio (1:1, 16:9, 9:16, 4:3, 3:4, etc.)
            size: Image size (1K, 2K, 4K)
            count: Number of images (1-4, Imagen only)
            reference: Optional reference image for editing/style

        Returns:
            GeneratedMedia with image bytes
        """
        model = model or self.MODELS['imagine']

        # Imagen models use generate_images API
        if model.startswith('imagen-'):
            return self._imagine_imagen(prompt, model, ratio, size, count)

        # Gemini models use generate_content with IMAGE modality
        return self._imagine_gemini(prompt, model, ratio, size, reference)

    def _imagine_imagen(
        self, prompt: str, model: str, ratio: str, size: str, count: int
    ) -> GeneratedMedia:
        """Generate image using Imagen 4 API."""
        config_args = {
            'numberOfImages': min(count, 4),
            'aspectRatio': ratio,
        }

        # Fast model doesn't support imageSize
        if 'fast' not in model.lower():
            config_args['imageSize'] = size

        try:
            response = self.client.models.generate_images(
                model=model,
                prompt=prompt,
                config=types.GenerateImagesConfig(**config_args),
            )
        except Exception as e:
            raise _wrap_generation_error(e, f"Image generation ({model})")

        # Return first image
        img = response.generated_images[0]
        return GeneratedMedia(
            data=img.image.image_bytes,
            mime_type='image/png',
            metadata={'model': model, 'ratio': ratio, 'count': len(response.generated_images)},
        )

    def _imagine_gemini(
        self, prompt: str, model: str, ratio: str, size: str, reference: Optional[any]
    ) -> GeneratedMedia:
        """Generate image using Gemini native image generation."""
        contents = []

        # Add reference image if provided
        if reference:
            ref_data, ref_mime = self._load_media(reference)
            contents.append(types.Part.from_bytes(data=ref_data, mime_type=ref_mime))

        contents.append(prompt)

        # Build image config
        img_config_args = {'aspect_ratio': ratio}
        # Only add size if model supports it
        if 'pro' in model.lower():
            img_config_args['image_size'] = size

        try:
            response = self.client.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=['IMAGE'],
                    image_config=types.ImageConfig(**img_config_args),
                ),
            )
        except Exception as e:
            raise _wrap_generation_error(e, f"Image generation ({model})")

        # Extract image from response
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                return GeneratedMedia(
                    data=part.inline_data.data,
                    mime_type='image/png',
                    metadata={'model': model, 'ratio': ratio},
                )

        raise RuntimeError("No image generated")

    def video(
        self,
        prompt: str,
        model: Optional[str] = None,
        resolution: str = "1080p",
        ratio: str = "16:9",
        start_frame: Optional[Union[str, Path, bytes]] = None,
        end_frame: Optional[Union[str, Path, bytes]] = None,
    ) -> GeneratedMedia:
        """
        Generate video from text prompt.

        Args:
            prompt: Description of desired video
            model: Model to use (default: veo-3.1-generate-preview)
            resolution: Video resolution (720p, 1080p)
            ratio: Aspect ratio (16:9, 9:16, 1:1)
            start_frame: Optional starting frame image
            end_frame: Optional ending frame for interpolation

        Returns:
            GeneratedMedia with video bytes
        """
        model = model or self.MODELS['video']

        config_args = {
            'aspect_ratio': ratio,
            'resolution': resolution,
        }

        # Load frames if provided
        first_frame = None
        if start_frame:
            frame_data, frame_mime = self._load_media(start_frame)
            first_frame = types.Image(image_bytes=frame_data, mime_type=frame_mime)

        if end_frame:
            end_data, end_mime = self._load_media(end_frame)
            config_args['last_frame'] = types.Image(image_bytes=end_data, mime_type=end_mime)

        # Start generation
        try:
            operation = self.client.models.generate_videos(
                model=model,
                prompt=prompt,
                image=first_frame,
                config=types.GenerateVideosConfig(**config_args),
            )

            # Poll until complete
            while not operation.done:
                time.sleep(5)
                operation = self.client.operations.get(operation)

            # Download result
            video = operation.response.generated_videos[0]
            self.client.files.download(file=video.video)
        except (BillingError, FreeTierQuotaError):
            raise  # Re-raise our custom errors
        except Exception as e:
            raise _wrap_generation_error(e, f"Video generation ({model})")

        # Save to temp and read
        temp_path = self._output_dir / f"video_{int(time.time())}.mp4"
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        video.video.save(str(temp_path))

        return GeneratedMedia(
            data=temp_path.read_bytes(),
            path=str(temp_path),
            mime_type='video/mp4',
            metadata={'model': model, 'resolution': resolution, 'ratio': ratio},
        )

    def transcribe(
        self,
        source: Union[str, Path, bytes],
        model: Optional[str] = None,
        timestamps: bool = True,
        speakers: bool = False,
        language: Optional[str] = None,
    ) -> ProcessResult:
        """
        Transcribe audio or video to text.

        Args:
            source: Audio/video file path or bytes
            model: Override default model
            timestamps: Include timestamps in output
            speakers: Identify different speakers
            language: Target language for transcription

        Returns:
            ProcessResult with transcription text
        """
        parts = []
        if timestamps:
            parts.append("with timestamps in [HH:MM:SS] format")
        if speakers:
            parts.append("identifying different speakers")
        if language:
            parts.append(f"in {language}")

        prompt = f"Transcribe this {'audio' if self._is_audio(source) else 'video'} {', '.join(parts)}."

        return self.process(source, prompt, model=model or self.MODELS['transcribe'])

    def _is_audio(self, source: Union[str, Path, bytes]) -> bool:
        """Check if source is audio based on extension."""
        if isinstance(source, (str, Path)):
            ext = Path(source).suffix.lower()
            return ext in {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'}
        return False

    def convert(
        self,
        source: Union[str, Path, bytes],
        output_format: str = "markdown",
        model: Optional[str] = None,
    ) -> ProcessResult:
        """
        Convert document to structured format.

        Args:
            source: Document file (PDF, DOCX, etc.)
            output_format: Target format (markdown, json, text)
            model: Override default model

        Returns:
            ProcessResult with converted content
        """
        format_instructions = {
            'markdown': "Convert to clean markdown, preserving structure and formatting.",
            'json': "Extract content as structured JSON with sections, paragraphs, and metadata.",
            'text': "Extract plain text content, maintaining logical reading order.",
        }

        prompt = format_instructions.get(output_format, format_instructions['markdown'])
        return self.process(source, prompt, model=model, output_json=(output_format == 'json'))


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Unified Multimodal I/O',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest='command', required=True)

    # Process command
    proc = subparsers.add_parser('process', help='Process media with prompt')
    proc.add_argument('file', help='Input file path or YouTube URL')
    proc.add_argument('--prompt', '-p', required=True, help='Processing prompt')
    proc.add_argument('--model', '-m', help='Model override')
    proc.add_argument('--json', action='store_true', help='Output JSON')
    proc.add_argument('--output', '-o', help='Save result to file (markdown)')

    # Imagine command
    img = subparsers.add_parser('imagine', help='Generate image')
    img.add_argument('prompt', help='Image description')
    img.add_argument('--model', '-m', help='Model override')
    img.add_argument('--ratio', '-r', default='1:1', help='Aspect ratio')
    img.add_argument('--size', '-s', default='1K', help='Image size')
    img.add_argument('--output', '-o', help='Output file path')

    # Video command
    vid = subparsers.add_parser('video', help='Generate video')
    vid.add_argument('prompt', help='Video description')
    vid.add_argument('--model', '-m', help='Model override')
    vid.add_argument('--resolution', default='1080p', help='Resolution')
    vid.add_argument('--ratio', '-r', default='16:9', help='Aspect ratio')
    vid.add_argument('--output', '-o', help='Output file path')

    # Transcribe command
    trans = subparsers.add_parser('transcribe', help='Transcribe audio/video')
    trans.add_argument('file', help='Input file path')
    trans.add_argument('--timestamps', '-t', action='store_true', help='Include timestamps')
    trans.add_argument('--speakers', action='store_true', help='Identify speakers')
    trans.add_argument('--output', '-o', help='Output file path')

    # Convert command
    conv = subparsers.add_parser('convert', help='Convert document')
    conv.add_argument('file', help='Input file path')
    conv.add_argument('--format', '-f', default='markdown', choices=['markdown', 'json', 'text'])
    conv.add_argument('--output', '-o', help='Output file path')

    args = parser.parse_args()

    try:
        mm = MMIO()

        if args.command == 'process':
            result = mm.process(args.file, args.prompt, model=args.model, output_json=args.json)
            if args.output:
                Path(args.output).parent.mkdir(parents=True, exist_ok=True)
                Path(args.output).write_text(result.text, encoding='utf-8')
                print(f"Saved: {args.output}")
            else:
                print(result.text)

        elif args.command == 'imagine':
            media = mm.imagine(args.prompt, model=args.model, ratio=args.ratio, size=args.size)
            out = args.output or f"generated_{int(time.time())}.png"
            media.save(out)
            print(f"Saved: {out}")

        elif args.command == 'video':
            media = mm.video(args.prompt, model=args.model, resolution=args.resolution, ratio=args.ratio)
            out = args.output or media.path
            if args.output:
                media.save(out)
            print(f"Saved: {out}")

        elif args.command == 'transcribe':
            result = mm.transcribe(args.file, timestamps=args.timestamps, speakers=args.speakers)
            if args.output:
                Path(args.output).write_text(result.text)
                print(f"Saved: {args.output}")
            else:
                print(result.text)

        elif args.command == 'convert':
            result = mm.convert(args.file, output_format=args.format)
            if args.output:
                Path(args.output).write_text(result.text)
                print(f"Saved: {args.output}")
            else:
                print(result.text)

    except (BillingError, FreeTierQuotaError) as e:
        # Clear, actionable error messages for billing issues
        print(str(e), file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()