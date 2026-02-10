import sys
import time
import wave
from pathlib import Path

import requests


# Add src to path to import config
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))

from config import ProjectConfig


settings = ProjectConfig.get_settings()
host = settings.HOST if settings.HOST != "0.0.0.0" else "localhost"
ENDPOINT = f"http://{host}:{settings.PORT}/generate/base/stream/0.6b"
OUTPUT_DIR = settings.OUTPUT_DIR
HTTP_OK = 200


def test_stream() -> None:
    """Tests HTTP chunked streaming with metrics and WAV conversion."""
    # Payload matching BaseGenerateRequest
    payload = {
        "text": (
            "Dies ist ein deutlich längerer Text, um das Streaming besser zu testen. "
            "Wir wollen überprüfen, ob die Latenz stabil bleibt und die "
            "Audioqualität konstant ist. "
            "Durch die längere Generierung können wir die Antwortzeiten und den "
            "Puffer besser analysieren. Ich hoffe, das Ergebnis entspricht nun den "
            "Erwartungen."
        ),
        "language": "German",
    }
    print("Testing HTTP stream with 0.6B model...")

    start_time = time.time()
    ttfb = 0.0
    total_audio_bytes = 0
    chunk_timestamps = []

    try:
        with requests.post(ENDPOINT, json=payload, stream=True) as r:
            if r.status_code == HTTP_OK:
                raw_path = OUTPUT_DIR / "test_stream_output.raw"
                wav_path = OUTPUT_DIR / "test_stream_output.wav"
                OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

                # Collect all chunks
                chunks = []
                chunk_count = 0

                print("Waiting for first byte...")
                iter_content = r.iter_content(chunk_size=4096)

                # Manual iteration to catch TTFB
                try:
                    first_chunk = next(iter_content)
                    ttfb = time.time() - start_time
                    chunk_timestamps.append(time.time())
                    print(f"TTFB: {ttfb * 1000:.2f}ms")

                    if first_chunk:
                        chunks.append(first_chunk)
                        total_audio_bytes += len(first_chunk)
                        chunk_count += 1
                except StopIteration:
                    print("No data received.")
                    return

                for chunk in iter_content:
                    if chunk:
                        chunks.append(chunk)
                        total_audio_bytes += len(chunk)
                        chunk_count += 1
                        chunk_timestamps.append(time.time())
                        if chunk_count % 10 == 0:
                            print(f"Received {chunk_count} chunks...", end="\r")

                total_time = time.time() - start_time
                print(f"\nTotal chunks: {chunk_count}")

                # Save RAW
                with raw_path.open("wb") as f:
                    for chunk in chunks:
                        f.write(chunk)
                print(f"Raw PCM saved to {raw_path}")

                # Save WAV
                # Audio settings from server: 24kHz, 1 channel, 16-bit (2 bytes)
                sample_rate = 24000
                num_channels = 1
                sample_width = 2

                with wave.open(str(wav_path), "wb") as wf:
                    wf.setnchannels(num_channels)
                    wf.setsampwidth(sample_width)
                    wf.setframerate(sample_rate)
                    wf.writeframes(b"".join(chunks))

                print(f"WAV audio saved to {wav_path}")

                # Metrics
                audio_duration = total_audio_bytes / (
                    sample_rate * num_channels * sample_width
                )
                rtf = total_time / audio_duration if audio_duration > 0 else 0

                # Calculate avg chunk time (inter-chunk arrival time)
                if len(chunk_timestamps) > 1:
                    deltas = [
                        t2 - t1
                        for t1, t2 in zip(
                            chunk_timestamps[:-1], chunk_timestamps[1:], strict=True
                        )
                    ]
                    avg_delta = sum(deltas) / len(deltas)
                else:
                    avg_delta = 0

                print("\n=== Performance Metrics ===")
                print(f"TTFB:            {ttfb * 1000:.2f} ms")
                print(f"Total Time:      {total_time:.2f} s")
                print(f"Audio Duration:  {audio_duration:.2f} s")
                print(
                    f"RTF:             {rtf:.2f} (lower is better, < 1.0 is real-time)"
                )
                print(f"Avg Chunk Delta: {avg_delta * 1000:.2f} ms")
                print("===========================")

            else:
                print(f"Failed: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_stream()
