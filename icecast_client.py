"""
Icecast Source Client
Connects to Icecast server and streams encoded audio with metadata support
Uses ffmpeg subprocess for reliable encoding and streaming
"""

import asyncio
import subprocess
import sys
from typing import Optional
from pathlib import Path


class IcecastSourceClient:
    """
    Client that streams audio to an Icecast server.
    Uses ffmpeg to encode PCM audio to MP3 and stream via HTTP PUT.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8000,
        mount: str = "/radio.mp3",
        source_password: str = "hackme",
        format: str = "mp3",
        bitrate: int = 128,
        sample_rate: int = 24000
    ):
        """
        Initialize Icecast source client.

        Args:
            host: Icecast server hostname
            port: Icecast server port
            mount: Mount point path (e.g., /radio.mp3)
            source_password: Password for source authentication
            format: Audio format (mp3 or ogg)
            bitrate: Bitrate in kbps
            sample_rate: Audio sample rate
        """
        self.host = host
        self.port = port
        self.mount = mount
        self.source_password = source_password
        self.format = format
        self.bitrate = bitrate
        self.sample_rate = sample_rate

        self.url = f"http://{host}:{port}{mount}"
        self.running = False
        self.ffmpeg_process: Optional[subprocess.Popen] = None
        self.current_metadata: Optional[str] = None

    def _build_ffmpeg_command(self) -> list[str]:
        """
        Build ffmpeg command for streaming to Icecast.

        Returns:
            List of command arguments for ffmpeg
        """
        # Build Icecast URL with authentication
        # Format: http://source:password@host:port/mount
        auth_url = f"http://source:{self.source_password}@{self.host}:{self.port}{self.mount}"
        
        # FFmpeg command to read raw PCM from stdin and stream to Icecast
        # Note: ffmpeg uses HTTP PUT method automatically for Icecast streams
        # For MP3 encoding, we need to specify the codec
        if self.format == "mp3":
            # Use libmp3lame encoder for MP3
            cmd = [
                "ffmpeg",
                "-f", "s16le",  # Input format: 16-bit signed little-endian PCM
                "-ar", str(self.sample_rate),  # Sample rate
                "-ac", "1",  # Mono audio
                "-i", "pipe:0",  # Read from stdin
                "-codec:a", "libmp3lame",  # MP3 encoder
                "-b:a", f"{self.bitrate}k",  # Audio bitrate
                "-f", "mp3",  # Output format
                "-content_type", "audio/mpeg",
                "-reconnect", "1",  # Auto-reconnect on disconnect
                "-reconnect_at_eof", "1",  # Reconnect at end of stream
                "-reconnect_streamed", "1",  # Reconnect for streaming
                "-reconnect_delay_max", "2",  # Max reconnect delay
                auth_url
            ]
        else:
            # For Ogg Vorbis
            cmd = [
                "ffmpeg",
                "-f", "s16le",
                "-ar", str(self.sample_rate),
                "-ac", "1",
                "-i", "pipe:0",
                "-codec:a", "libvorbis",
                "-b:a", f"{self.bitrate}k",
                "-f", "ogg",
                "-content_type", "audio/ogg",
                "-reconnect", "1",
                "-reconnect_at_eof", "1",
                "-reconnect_streamed", "1",
                "-reconnect_delay_max", "2",
                auth_url
            ]
        return cmd

    async def start(self):
        """Start the Icecast client and ffmpeg process."""
        if self.running:
            return

        try:
            cmd = self._build_ffmpeg_command()
            self.ffmpeg_process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0
            )
            self.running = True
            print(f"✅ Started Icecast client, streaming to {self.url}")
        except FileNotFoundError:
            print("❌ Error: ffmpeg not found. Please install ffmpeg.")
            print("   On Ubuntu/Debian: sudo apt-get install ffmpeg")
            self.running = False
        except Exception as e:
            print(f"❌ Error starting Icecast client: {e}")
            self.running = False

    async def send_audio_chunk(self, pcm_data: bytes, metadata: Optional[str] = None):
        """
        Send audio chunk to Icecast server via ffmpeg.

        Args:
            pcm_data: Raw PCM audio data (16-bit, mono)
            metadata: Optional metadata string (track name)
        """
        if not self.running:
            return

        # Check if process is still alive
        if self.ffmpeg_process and self.ffmpeg_process.poll() is not None:
            # Process has exited
            return_code = self.ffmpeg_process.returncode
            print(f"⚠️ FFmpeg process exited with code {return_code}")
            if return_code != 0:
                # Read stderr for error messages
                if self.ffmpeg_process.stderr:
                    try:
                        stderr = self.ffmpeg_process.stderr.read().decode('utf-8', errors='ignore')
                        if stderr:
                            print(f"FFmpeg error: {stderr[:500]}")
                    except:
                        pass
            # Try to restart
            if self.running:
                print("🔄 Attempting to restart Icecast client...")
                await self.stop()
                await self.start()
            return

        if not self.ffmpeg_process or not self.ffmpeg_process.stdin:
            return

        # Update metadata if changed
        if metadata and metadata != self.current_metadata:
            self.current_metadata = metadata
            print(f"📻 Now playing: {metadata}")
            # Note: Metadata updates via ffmpeg require different approach
            # For now, we just log it

        try:
            # Write PCM data to ffmpeg stdin
            self.ffmpeg_process.stdin.write(pcm_data)
            self.ffmpeg_process.stdin.flush()
        except BrokenPipeError:
            print("❌ Icecast connection broken, attempting to restart...")
            if self.running:
                await self.stop()
                await self.start()
        except OSError as e:
            # Process may have terminated
            if self.running:
                print(f"❌ Error writing to ffmpeg: {e}")
        except Exception as e:
            print(f"❌ Error sending audio chunk: {e}")

    async def stop(self):
        """Stop the Icecast client and ffmpeg process."""
        self.running = False

        if self.ffmpeg_process:
            try:
                # Close stdin to signal end of stream
                if self.ffmpeg_process.stdin:
                    self.ffmpeg_process.stdin.close()
                
                # Wait for process to finish (with timeout)
                try:
                    self.ffmpeg_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't stop
                    self.ffmpeg_process.kill()
                    self.ffmpeg_process.wait()

                # Check for errors
                if self.ffmpeg_process.returncode != 0:
                    stderr = self.ffmpeg_process.stderr.read().decode() if self.ffmpeg_process.stderr else ""
                    if stderr and "error" in stderr.lower():
                        print(f"⚠️ FFmpeg errors: {stderr[:200]}")

            except Exception as e:
                print(f"⚠️ Error stopping ffmpeg process: {e}")
            finally:
                self.ffmpeg_process = None

        print("🛑 Icecast client stopped")

    def is_connected(self) -> bool:
        """Check if client is connected and running."""
        return self.running and self.ffmpeg_process is not None and self.ffmpeg_process.poll() is None

