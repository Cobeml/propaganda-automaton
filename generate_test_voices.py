"""
Generate test voice tracks for the radio
"""

from audio_gen import generate_audio

# Sample radio announcements
announcements = [
    {
        "text": "Welcome to Martian Radio, broadcasting live from the red planet. Stay tuned for more updates.",
        "filename": "voices/01_welcome.wav",
        "voice": "am_adam"
    },
    {
        "text": "This is your host bringing you the latest news from Mars Colony Alpha. The weather today is clear with minimal dust storms.",
        "filename": "voices/02_weather.wav",
        "voice": "am_michael"
    },
    {
        "text": "Remember to check your oxygen levels and keep your suits maintained. Safety first, colonists.",
        "filename": "voices/03_safety.wav",
        "voice": "af_bella"
    },
]

def main():
    print("Generating test voice tracks for radio...")
    print("=" * 60)

    for i, announcement in enumerate(announcements, 1):
        print(f"\n[{i}/{len(announcements)}] Generating: {announcement['filename']}")
        print(f"Voice: {announcement['voice']}")
        print(f"Text: {announcement['text'][:60]}...")

        generate_audio(
            text=announcement['text'],
            output_path=announcement['filename'],
            voice=announcement['voice'],
            lang_code='a',
            speed=1.0
        )

    print("\n" + "=" * 60)
    print("✅ All voice tracks generated successfully!")
    print("You can now start the radio with: python radio.py")

if __name__ == "__main__":
    main()
