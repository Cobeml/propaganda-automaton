"""
Audio Mixer for Radio Station
Mixes background music with voice tracks and generates continuous stream
"""

import numpy as np
import soundfile as sf
from pathlib import Path
from typing import Iterator, List
import io


class RadioMixer:
    """Mixes background music with voice tracks for radio streaming"""

    def __init__(
        self,
        music_file: Path,
        voices_dir: Path,
        music_volume: float = 0.2,
        voice_volume: float = 1.0,
        pause_duration: float = 10.0,
        sample_rate: int = 24000
    ):
        """
        Initialize the radio mixer.

        Args:
            music_file: Path to background music file
            voices_dir: Directory containing voice track files
            music_volume: Volume multiplier for background music (0.0-1.0)
            voice_volume: Volume multiplier for voice tracks (0.0-1.0)
            pause_duration: Seconds of silence between voice tracks
            sample_rate: Audio sample rate (default 24000 Hz)
        """
        self.music_file = music_file
        self.voices_dir = voices_dir
        self.music_volume = music_volume
        self.voice_volume = voice_volume
        self.pause_duration = pause_duration
        self.sample_rate = sample_rate

        # Load background music
        self.music_data, self.music_sr = sf.read(str(music_file))
        if self.music_sr != sample_rate:
            print(f"Warning: Music sample rate {self.music_sr} != {sample_rate}")

        # Convert to mono if stereo
        if len(self.music_data.shape) > 1:
            self.music_data = np.mean(self.music_data, axis=1)

        # Get voice files
        self.voice_files = sorted(voices_dir.glob("*.wav"))
        print(f"Found {len(self.voice_files)} voice tracks")

        # Generate silence for pauses
        self.pause_samples = int(pause_duration * sample_rate)
        self.silence = np.zeros(self.pause_samples, dtype=np.float32)

    def _get_music_segment(self, length: int, offset: int) -> np.ndarray:
        """
        Get a segment of background music with looping.

        Args:
            length: Number of samples needed
            offset: Starting position in music

        Returns:
            Music segment of requested length
        """
        music_length = len(self.music_data)
        segment = np.zeros(length, dtype=np.float32)

        current_offset = offset % music_length
        remaining = length

        while remaining > 0:
            available = music_length - current_offset
            to_copy = min(remaining, available)

            segment[length - remaining:length - remaining + to_copy] = \
                self.music_data[current_offset:current_offset + to_copy]

            remaining -= to_copy
            current_offset = 0  # Loop back to start

        return segment * self.music_volume

    def _mix_voice_with_music(
        self, voice_data: np.ndarray, music_offset: int
    ) -> tuple[np.ndarray, int]:
        """
        Mix voice audio with background music.

        Args:
            voice_data: Voice audio samples
            music_offset: Current position in background music

        Returns:
            Mixed audio and new music offset
        """
        voice_length = len(voice_data)

        # Get corresponding music segment
        music_segment = self._get_music_segment(voice_length, music_offset)

        # Scale voice volume
        scaled_voice = voice_data * self.voice_volume

        # Mix by adding
        mixed = music_segment + scaled_voice

        # Prevent clipping
        max_val = np.max(np.abs(mixed))
        if max_val > 1.0:
            mixed = mixed / max_val

        new_offset = (music_offset + voice_length) % len(self.music_data)

        return mixed, new_offset

    def generate_stream(self, chunk_size: int = 8192) -> Iterator[bytes]:
        """
        Generate infinite mixed audio stream.

        Args:
            chunk_size: Size of each chunk in samples

        Yields:
            Audio data chunks as bytes
        """
        music_offset = 0

        while True:  # Infinite loop for radio
            # Play all voice tracks in order
            for voice_file in self.voice_files:
                print(f"Now playing: {voice_file.name}")

                # Load voice track
                voice_data, voice_sr = sf.read(str(voice_file))

                if voice_sr != self.sample_rate:
                    print(f"Warning: Voice sample rate {voice_sr} != {self.sample_rate}")

                # Convert to mono if stereo
                if len(voice_data.shape) > 1:
                    voice_data = np.mean(voice_data, axis=1)

                # Mix voice with music
                mixed_audio, music_offset = self._mix_voice_with_music(
                    voice_data, music_offset
                )

                # Stream mixed audio in chunks
                total_samples = len(mixed_audio)
                for i in range(0, total_samples, chunk_size):
                    chunk = mixed_audio[i:i + chunk_size]

                    # Convert to bytes
                    buffer = io.BytesIO()
                    sf.write(buffer, chunk, self.sample_rate, format='WAV')
                    buffer.seek(0)

                    # Skip WAV header for subsequent chunks
                    if i > 0:
                        buffer.seek(44)  # Skip WAV header

                    yield buffer.read()

                # Add pause with background music
                print(f"  Pause ({self.pause_duration}s)...")
                pause_with_music = self._get_music_segment(
                    self.pause_samples, music_offset
                )
                music_offset = (music_offset + self.pause_samples) % len(self.music_data)

                # Stream pause in chunks
                for i in range(0, len(pause_with_music), chunk_size):
                    chunk = pause_with_music[i:i + chunk_size]

                    buffer = io.BytesIO()
                    sf.write(buffer, chunk, self.sample_rate, format='WAV')
                    buffer.seek(0)

                    if i > 0:
                        buffer.seek(44)

                    yield buffer.read()

            print("Voice playlist completed, looping...")


def test_mixer():
    """Test the audio mixer"""
    music_file = Path("music/Martian_Elevator_Loop_2025-11-08T144229.wav")
    voices_dir = Path("voices")

    if not music_file.exists():
        print(f"Error: Music file not found: {music_file}")
        return

    if not voices_dir.exists() or not list(voices_dir.glob("*.wav")):
        print(f"Error: No voice files found in {voices_dir}")
        return

    mixer = RadioMixer(
        music_file=music_file,
        voices_dir=voices_dir,
        music_volume=0.2,
        voice_volume=1.0,
        pause_duration=10.0
    )

    # Test: generate a short sample
    print("Testing mixer...")
    stream = mixer.generate_stream()

    # Get first few chunks
    for i, chunk in enumerate(stream):
        print(f"Generated chunk {i}, size: {len(chunk)} bytes")
        if i >= 3:  # Just test a few chunks
            break

    print("Mixer test complete!")


if __name__ == "__main__":
    test_mixer()
