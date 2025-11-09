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
        voices_dir: Path = None,
        recurring_voice_files: list = None,
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
            voices_dir: Directory with voice tracks (deprecated)
            recurring_voice_files: List of voice file paths that loop
            music_volume: Background music volume
            voice_volume: Voice track volume
            pause_duration: Seconds between tracks
            chunk_size: Size of audio chunks
            buffer_size: Number of chunks to keep in buffer
        """
        self.mixer = RadioMixer(
            music_file=music_file,
            voices_dir=voices_dir,
            recurring_voice_files=recurring_voice_files,
            music_volume=music_volume,
            voice_volume=voice_volume,
            pause_duration=pause_duration
        )

        self.chunk_size = chunk_size
        self.buffer_size = buffer_size
        self.sample_rate = 24000  # Match audio_mixer sample rate
        
        # Calculate seconds per chunk for playback time tracking
        # chunk_size is in samples, sample_rate is samples per second
        self.seconds_per_chunk = chunk_size / self.sample_rate

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
        
        # Track playback position for logging (based on actual playback time)
        self.playback_chunks_sent = 0
        self.last_logged_track = None
        self.last_logged_paused = None
        self.last_log_time = time.time()

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

    def _check_and_log_state_change(self, new_track: str, new_paused: bool):
        """
        Check if state has changed and log it.
        This ensures we only log once per state change, not per chunk.
        """
        # Track state changes based on what's being added to buffer
        # We log when we START generating a new track/pause, which represents
        # what will be played soon (since generation is slightly ahead of playback)
        if new_track != self.last_logged_track:
            print(f"🎵 Now playing: {new_track}")
            self.last_logged_track = new_track
            self.last_logged_paused = None  # Reset pause state when track changes
        
        if new_paused != self.last_logged_paused:
            if new_paused:
                print(f"⏸️  Pause ({self.mixer.pause_duration}s)...")
            self.last_logged_paused = new_paused

    async def _broadcast_loop(self):
        """
        Background task that continuously generates audio chunks.
        Generates at approximately real-time speed to keep logs synchronized
        with actual playback timing.
        """
        print("🎵 Starting continuous audio generation...")

        try:
            # Generate audio stream
            stream = self.mixer.generate_stream(chunk_size=self.chunk_size)
            last_track = None
            last_paused = None
            last_chunk_time = time.time()
            header_sent = False

            for chunk in stream:
                if not self.running:
                    break

                # Skip state tracking for WAV header (first chunk)
                if not header_sent:
                    header_sent = True
                    # Add header to buffer but don't update track state yet
                    self.buffer.append({
                        'seq': self.current_seq,
                        'data': chunk,
                        'timestamp': time.time(),
                        'track': None,  # Header has no track
                        'paused': False
                    })
                    self.current_seq += 1
                    self.new_chunk_event.set()
                    await asyncio.sleep(0.001)  # Minimal delay for header
                    continue

                # Get current track info from mixer (should be set by now)
                current_track = self.mixer.current_track
                is_paused = self.mixer.is_paused

                # Always add chunk to buffer (even if track is None initially)
                self.buffer.append({
                    'seq': self.current_seq,
                    'data': chunk,
                    'timestamp': time.time(),
                    'track': current_track,
                    'paused': is_paused
                })

                self.current_seq += 1

                # Update broadcast state (used by get_current_track() API)
                # Only update if we have a real track (not None)
                if current_track is not None:
                    self.broadcast_track = current_track
                    self.broadcast_paused = is_paused

                    # Log state changes when they occur (once per state change)
                    if current_track != last_track or is_paused != last_paused:
                        self._check_and_log_state_change(current_track, is_paused)
                        last_track = current_track
                        last_paused = is_paused

                # Signal that new chunk is available
                self.new_chunk_event.set()

                # Wait approximately the duration of this chunk to generate at real-time speed
                # This ensures logs appear at the right time relative to playback
                current_time = time.time()
                elapsed = current_time - last_chunk_time
                sleep_time = max(0, self.seconds_per_chunk - elapsed)
                
                # Only sleep if we're generating faster than real-time
                # If buffer is getting low, we can generate faster
                if len(self.buffer) < self.buffer_size * 0.5:
                    # Buffer is getting low, generate faster (minimal sleep)
                    await asyncio.sleep(0.001)
                else:
                    # Buffer is healthy, generate at real-time speed
                    await asyncio.sleep(sleep_time)
                
                last_chunk_time = time.time()

        except Exception as e:
            print(f"❌ Error in broadcast loop: {e}")
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

        # Only log client subscriptions occasionally to avoid spam
        # (Removed verbose logging for each client connection)

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

    def add_sponsored_message(self, audio_file_path: str):
        """
        Add a one-time sponsored message to the broadcast queue.
        Will play after the current track finishes.
        
        Args:
            audio_file_path: Path to the sponsored audio file
        """
        self.mixer.add_sponsored_message(audio_file_path)


# Global broadcast instance
_broadcast_instance = None


def get_broadcast(
    music_file: Path = None,
    voices_dir: Path = None,
    recurring_voice_files: list = None,
    music_volume: float = 0.15,
    voice_volume: float = 1.0,
    pause_duration: float = 10.0
) -> SharedRadioBroadcast:
    """Get or create the global broadcast instance"""
    global _broadcast_instance

    if _broadcast_instance is None:
        if music_file is None:
            raise ValueError("Must provide music_file on first call")
        
        if voices_dir is None and recurring_voice_files is None:
            raise ValueError("Must provide either voices_dir or recurring_voice_files on first call")

        _broadcast_instance = SharedRadioBroadcast(
            music_file=music_file,
            voices_dir=voices_dir,
            recurring_voice_files=recurring_voice_files,
            music_volume=music_volume,
            voice_volume=voice_volume,
            pause_duration=pause_duration
        )

    return _broadcast_instance
