"""
Kokoro TTS Audio Generation Script
Simple utility for generating text-to-speech audio using Kokoro-82M model.
"""

from kokoro import KPipeline
import soundfile as sf
import torch
from pathlib import Path


def generate_audio(
    text: str,
    output_path: str = "voices/output.wav",
    voice: str = "bm_lewis",
    lang_code: str = "a",
    speed: float = 1.0,
    split_pattern: str = r'\n+'
) -> list[str]:
    """
    Generate audio from text using Kokoro TTS.

    Args:
        text: The text to convert to speech
        output_path: Base path for output files (default: "output.wav")
        voice: Voice to use (default: "af_heart")
               Available voices: af_heart, af_bella, af_sarah, af_nicole,
                                am_adam, am_michael, bf_emma, bf_isabella, etc.
        lang_code: Language code (default: "a" for American English)
                   'a' => American English 🇺🇸
                   'b' => British English 🇬🇧
                   'e' => Spanish 🇪🇸
                   'f' => French 🇫🇷
                   'h' => Hindi 🇮🇳
                   'i' => Italian 🇮🇹
                   'j' => Japanese 🇯🇵 (requires: pip install misaki[ja])
                   'p' => Brazilian Portuguese 🇧🇷
                   'z' => Mandarin Chinese 🇨🇳 (requires: pip install misaki[zh])
        speed: Speech speed multiplier (default: 1.0)
        split_pattern: Pattern to split text into segments (default: r'\n+')

    Returns:
        List of output file paths created
    """
    # Check GPU availability
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}")
    if device == 'cuda':
        print(f"GPU: {torch.cuda.get_device_name(0)}")

    # Initialize pipeline
    print(f"Initializing Kokoro pipeline with language '{lang_code}' and voice '{voice}'...")
    pipeline = KPipeline(lang_code=lang_code)

    # Generate audio
    print("Generating audio...")
    generator = pipeline(
        text,
        voice=voice,
        speed=speed,
        split_pattern=split_pattern
    )

    # Save audio files
    output_files = []
    output_base = Path(output_path).stem
    output_dir = Path(output_path).parent
    output_ext = Path(output_path).suffix or ".wav"

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    for i, (gs, ps, audio) in enumerate(generator):
        if len(list(generator)) > 1 or i > 0:
            # Multiple segments, add index
            file_path = output_dir / f"{output_base}_{i}{output_ext}"
        else:
            # Single segment, use original name
            file_path = output_path

        print(f"Segment {i}: {gs[:60]}..." if len(gs) > 60 else f"Segment {i}: {gs}")
        sf.write(str(file_path), audio, 24000)
        output_files.append(str(file_path))
        print(f"  Saved to: {file_path}")

    print(f"\nAudio generation complete! Generated {len(output_files)} file(s).")
    return output_files


def main():
    """Example usage of the audio generation function."""

    # Example 1: Simple text-to-speech
    text = """
    Kokoro is an open-weight TTS model with 82 million parameters.
    Despite its lightweight architecture, it delivers comparable quality to larger models
    while being significantly faster and more cost-efficient.
    """

    generate_audio(
        text=text,
        output_path="voices/kokoro_demo.wav",
        voice="bm_lewis",
        lang_code="a",
        speed=1.0
    )

    # Example 2: Multiple paragraphs (will create separate files)
    # long_text = """
    # This is paragraph one. It will be in one audio file.
    #
    # This is paragraph two. It will be in another audio file.
    # """
    #
    # generate_audio(
    #     text=long_text,
    #     output_path="multi_segment.wav",
    #     voice="am_adam",
    #     lang_code="a"
    # )


if __name__ == "__main__":
    main()
