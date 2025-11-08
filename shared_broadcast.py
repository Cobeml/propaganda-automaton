"""
Shared Radio Broadcast
Manages a single continuous audio stream that all clients tap into
"""

import asyncio
from collections import deque
from pathlib import Path
from audio_mixer import RadioMixer
from typing import AsyncIterator
import time


class SharedRadioBroadcast:
    """
    A shared radio broadcast that all clients can tap into.
    Continuously generates audio in the background and clients
    join at the current position.
    """

    def __init__(
        self,
        music_file: Path,
        voices_dir: Path,
        music_volume: float = 0.15,
        voice_volume: float = 1.0,
        pause_duration: float = 10.0,
        chunk_size: int = 8192,
        buffer_size: int = 100
    ):
        """
        Initialize the shared broadcast.

        Args:
            music_file: Path to background music
            voices_dir: Directory with voice tracks
            music_volume: Background music volume
            voice_volume: Voice track volume
            pause_duration: Seconds between tracks
            chunk_size: Size of audio chunks
            buffer_size: Number of chunks to keep in buffer
        """
        self.mixer = RadioMixer(
            music_file=music_file,
            voices_dir=voices_dir,
            music_volume=music_volume,
            voice_volume=voice_volume,
            pause_duration=pause_duration
        )

        self.chunk_size = chunk_size
        self.buffer_size = buffer_size

        # Circular buffer to store recent chunks
        self.buffer = deque(maxlen=buffer_size)

        # Event to signal new chunks available
        self.new_chunk_event = asyncio.Event()

        # Current chunk sequence number
        self.current_seq = 0

        # Track what's actually being broadcast (not just generated)
        self.last_broadcast_seq = -1
        self.broadcast_track = None
        self.broadcast_paused = False

        # Background task
        self.broadcast_task = None
        self.running = False

        # WAV header (sent once to new clients)
        from audio_mixer import create_wav_header
        self.wav_header = create_wav_header(sample_rate=24000)

    async def start(self):
        """Start the background broadcast task"""
        if self.broadcast_task is None:
            self.running = True
            self.broadcast_task = asyncio.create_task(self._broadcast_loop())
            print("📻 Shared broadcast started")

    async def stop(self):
        """Stop the background broadcast task"""
        self.running = False
        if self.broadcast_task:
            self.broadcast_task.cancel()
            try:
                await self.broadcast_task
            except asyncio.CancelledError:
                pass
            print("📻 Shared broadcast stopped")

    async def _broadcast_loop(self):
        """
        Background task that continuously generates audio chunks.
        This runs independently and fills the buffer.
        """
        print("🎵 Starting continuous audio generation...")

        try:
            # Generate audio stream
            stream = self.mixer.generate_stream(chunk_size=self.chunk_size)

            for chunk in stream:
                if not self.running:
                    break

                # Get current track info from mixer
                current_track = self.mixer.current_track or "Waiting..."
                is_paused = self.mixer.is_paused

                # Add chunk to buffer with sequence number and track metadata
                self.buffer.append({
                    'seq': self.current_seq,
                    'data': chunk,
                    'timestamp': time.time(),
                    'track': current_track,
                    'paused': is_paused
                })

                self.current_seq += 1

                # Signal that new chunk is available
                self.new_chunk_event.set()

                # Small delay to prevent tight loop
                await asyncio.sleep(0.001)

        except Exception as e:
            print(f"Error in broadcast loop: {e}")
            raise

    async def subscribe(self) -> AsyncIterator[bytes]:
        """
        Subscribe to the broadcast stream.
        Yields audio chunks starting from current position.

        This allows clients to "tune in" to the live broadcast.
        """
        # First, send WAV header
        yield self.wav_header

        # Get current sequence number when client connects
        if self.buffer:
            # Start from the most recent chunk
            last_seq = self.current_seq - 1
        else:
            # No chunks yet, wait for first one
            last_seq = -1

        print(f"🎧 New client subscribed at sequence {last_seq}")

        # Stream chunks as they become available
        while self.running:
            # Wait for new chunks
            await self.new_chunk_event.wait()

            # Get all chunks newer than what we've sent
            new_chunks = [
                chunk for chunk in self.buffer
                if chunk['seq'] > last_seq
            ]

            # Send new chunks
            for chunk in sorted(new_chunks, key=lambda x: x['seq']):
                yield chunk['data']
                last_seq = chunk['seq']

                # Update broadcast state based on what's actually being sent
                if chunk['seq'] > self.last_broadcast_seq:
                    self.last_broadcast_seq = chunk['seq']
                    self.broadcast_track = chunk['track']
                    self.broadcast_paused = chunk['paused']

            # Clear event and wait for next batch
            self.new_chunk_event.clear()

    def get_current_track(self) -> tuple[str, bool]:
        """
        Get current track info based on what's actually being broadcast.

        Returns:
            Tuple of (track_name, is_paused)
        """
        if self.broadcast_track is None:
            return "Waiting for broadcast...", False

        return self.broadcast_track, self.broadcast_paused


# Global broadcast instance
_broadcast_instance = None


def get_broadcast(
    music_file: Path = None,
    voices_dir: Path = None,
    music_volume: float = 0.15,
    voice_volume: float = 1.0,
    pause_duration: float = 10.0
) -> SharedRadioBroadcast:
    """Get or create the global broadcast instance"""
    global _broadcast_instance

    if _broadcast_instance is None:
        if music_file is None or voices_dir is None:
            raise ValueError("Must provide music_file and voices_dir on first call")

        _broadcast_instance = SharedRadioBroadcast(
            music_file=music_file,
            voices_dir=voices_dir,
            music_volume=music_volume,
            voice_volume=voice_volume,
            pause_duration=pause_duration
        )

    return _broadcast_instance
