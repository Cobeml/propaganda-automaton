"""
Audio Mixer for Radio Station
Mixes background music with voice tracks and generates continuous stream
"""

import numpy as np
import soundfile as sf
from pathlib import Path
from typing import Iterator
import struct


def create_wav_header(sample_rate: int = 24000, num_channels: int = 1, bits_per_sample: int = 16):
    """
    Create a WAV file header for streaming.
    Uses maximum file size since we're streaming infinitely.
    """
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8

    # Use maximum size for infinite stream
    subchunk2_size = 0xFFFFFFFF - 36
    chunk_size = subchunk2_size + 36

    header = bytearray()
    header.extend(b'RIFF')
    header.extend(struct.pack('<I', chunk_size))
    header.extend(b'WAVE')
    header.extend(b'fmt ')
    header.extend(struct.pack('<I', 16))  # Subchunk1Size (16 for PCM)
    header.extend(struct.pack('<H', 1))   # AudioFormat (1 for PCM)
    header.extend(struct.pack('<H', num_channels))
    header.extend(struct.pack('<I', sample_rate))
    header.extend(struct.pack('<I', byte_rate))
    header.extend(struct.pack('<H', block_align))
    header.extend(struct.pack('<H', bits_per_sample))
    header.extend(b'data')
    header.extend(struct.pack('<I', subchunk2_size))

    return bytes(header)


class RadioMixer:
    """Mixes background music with voice tracks for radio streaming"""

    def __init__(
        self,
        music_file: Path,
        voices_dir: Path = None,
        recurring_voice_files: list = None,
        music_volume: float = 0.2,
        voice_volume: float = 1.0,
        pause_duration: float = 10.0,
        sample_rate: int = 24000
    ):
        """
        Initialize the radio mixer.

        Args:
            music_file: Path to background music file
            voices_dir: Directory containing voice track files (deprecated, use recurring_voice_files)
            recurring_voice_files: List of voice file paths that loop continuously
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

        # Resample music if needed
        if self.music_sr != sample_rate:
            print(f"Note: Music sample rate is {self.music_sr}Hz, target is {sample_rate}Hz")
            # For simplicity, we'll use it as-is, but log the difference

        # Convert to mono if stereo
        if len(self.music_data.shape) > 1:
            self.music_data = np.mean(self.music_data, axis=1)

        # Recurring voice files (loop continuously)
        if recurring_voice_files:
            self.voice_files = [Path(f) for f in recurring_voice_files]
        elif voices_dir:
            # Fallback to old behavior for compatibility
            self.voice_files = sorted(voices_dir.glob("*.wav"))
        else:
            self.voice_files = []
        
        print(f"Loaded {len(self.voice_files)} recurring voice tracks")

        # Queue for one-time sponsored messages (FIFO)
        self.sponsored_queue = []

        # Generate silence for pauses
        self.pause_samples = int(pause_duration * sample_rate)

        # Track current playback state
        self.current_track = None
        self.is_paused = False

    def add_sponsored_message(self, audio_file_path: str):
        """
        Add a one-time sponsored message to play next.
        
        Args:
            audio_file_path: Path to the sponsored audio file
        """
        self.sponsored_queue.append(Path(audio_file_path))
        print(f"📢 Added sponsored message to queue: {audio_file_path}")
        print(f"   Queue size: {len(self.sponsored_queue)}")

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
            mixed = mixed / max_val * 0.95  # Leave some headroom

        new_offset = (music_offset + voice_length) % len(self.music_data)

        return mixed, new_offset

    def _audio_to_pcm_bytes(self, audio_data: np.ndarray) -> bytes:
        """
        Convert floating point audio to 16-bit PCM bytes.

        Args:
            audio_data: Floating point audio samples (-1.0 to 1.0)

        Returns:
            16-bit PCM byte data
        """
        # Clip to valid range
        audio_data = np.clip(audio_data, -1.0, 1.0)

        # Convert to 16-bit PCM
        pcm_data = (audio_data * 32767).astype(np.int16)

        return pcm_data.tobytes()

    def _play_voice_track(self, voice_file: Path, music_offset: int, chunk_size: int) -> Iterator[tuple[bytes, int]]:
        """
        Play a single voice track with music mixing.
        
        Args:
            voice_file: Path to voice file
            music_offset: Current position in background music
            chunk_size: Size of audio chunks
            
        Yields:
            Tuple of (audio_chunk, new_music_offset)
        """
        # Update current track state
        self.current_track = voice_file.name
        self.is_paused = False

        # Load voice track
        voice_data, voice_sr = sf.read(str(voice_file))

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
            yield self._audio_to_pcm_bytes(chunk), music_offset

        # Add pause with background music
        self.is_paused = True

        pause_with_music = self._get_music_segment(
            self.pause_samples, music_offset
        )
        music_offset = (music_offset + self.pause_samples) % len(self.music_data)

        # Stream pause in chunks
        for i in range(0, len(pause_with_music), chunk_size):
            chunk = pause_with_music[i:i + chunk_size]
            yield self._audio_to_pcm_bytes(chunk), music_offset

    def generate_stream(self, chunk_size: int = 8192) -> Iterator[bytes]:
        """
        Generate infinite mixed audio stream as WAV data.
        Prioritizes sponsored messages (one-time) over recurring tracks.

        Args:
            chunk_size: Size of each chunk in samples

        Yields:
            Audio data chunks as bytes (first chunk includes WAV header)
        """
        # Send WAV header first
        yield create_wav_header(sample_rate=self.sample_rate)

        music_offset = 0
        first_track = True

        while True:  # Infinite loop for radio
            # Check for sponsored messages first (priority)
            if self.sponsored_queue:
                sponsored_file = self.sponsored_queue.pop(0)
                print(f"🎙️ Playing sponsored message: {sponsored_file.name}")
                print(f"   Remaining in queue: {len(self.sponsored_queue)}")
                
                for chunk, music_offset in self._play_voice_track(sponsored_file, music_offset, chunk_size):
                    yield chunk
                    
                continue  # Go back to check for more sponsored messages
            
            # Play recurring voice tracks
            for voice_file in self.voice_files:
                # Check for sponsored messages again before each regular track
                if self.sponsored_queue:
                    break  # Exit to prioritize sponsored message
                
                for chunk, music_offset in self._play_voice_track(voice_file, music_offset, chunk_size):
                    yield chunk

            # Playlist completed, will loop


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
        if i >= 5:  # Just test a few chunks
            break

    print("Mixer test complete!")


if __name__ == "__main__":
    test_mixer()
