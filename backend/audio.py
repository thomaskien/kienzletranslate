"""Bounded, in-memory PCM decoding. Never writes user audio to disk."""
import io
import math
import wave

MAX_BYTES = 16 * 1024 * 1024
MAX_SECONDS = 60


def inspect_wav(data: bytes):
    if not 44 <= len(data) <= MAX_BYTES:
        raise ValueError("Audio size is outside the permitted range")
    try:
        with wave.open(io.BytesIO(data), "rb") as wav:
            channels, width, rate, frames, compression, _ = wav.getparams()
            if channels != 1 or width != 2 or compression != "NONE":
                raise ValueError("Expected mono PCM16 WAV")
            if not 8000 <= rate <= 96000 or not 0 < frames <= rate * MAX_SECONDS:
                raise ValueError("Recording must be between 0 and 60 seconds")
            pcm = wav.readframes(frames)
            if len(pcm) != frames * width:
                raise ValueError("Truncated WAV")
            return pcm, rate, frames
    except (wave.Error, EOFError) as exc:
        raise ValueError("Invalid WAV") from exc


def decode_wav(data):
    import numpy as np
    from scipy.signal import resample_poly
    pcm, rate, frames = inspect_wav(data)
    samples = np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32768
    if rate != 16000:
        divisor = math.gcd(rate, 16000)
        samples = resample_poly(samples, 16000 // divisor, rate // divisor).astype(np.float32)
    return samples, frames / rate


def encode_wav(samples, rate=16000):
    import numpy as np
    output = io.BytesIO()
    pcm = (np.clip(samples, -1, 1) * 32767).astype("<i2").tobytes()
    with wave.open(output, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(pcm)
    return output.getvalue()
