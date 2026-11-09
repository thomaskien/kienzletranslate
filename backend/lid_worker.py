"""Isolated CPU-only Whisper base/VAD runtime. No recordings are written to disk."""
import sys
from multiprocessing.connection import Connection
from .lid import accepted_language, LANGUAGE_CODES


def identify(audio, model, speech_segments):
    if not speech_segments:
        return {'accepted': False, 'reason': 'no_speech'}
    start = speech_segments[0]['start']
    previous = None
    for seconds in (3, 5, 8):
        end = start + seconds * 16000
        if end > len(audio):
            break
        # Reject tiny amounts of speech padded by silence; retain internal pauses.
        speech = sum(max(0, min(s['end'], end) - max(s['start'], start)) for s in speech_segments)
        if speech < seconds * 16000 * .5:
            previous = None
            continue
        _, _, probabilities = model.detect_language(audio=audio[start:end], vad_filter=False,
                                                     language_detection_segments=1)
        pairs = probabilities.items() if hasattr(probabilities, 'items') else probabilities
        ranked = sorted(pairs, key=lambda item: (-item[1], item[0]))
        current = {'language': ranked[0][0], 'score': float(ranked[0][1]),
                   'margin': float(ranked[0][1] - ranked[1][1]) if len(ranked) > 1 else 0}
        code = accepted_language(previous, current)
        if code:
            return {'accepted': True, 'language': code, 'audio_seconds': seconds}
        if (previous and previous['language'] == current['language']
                and current['language'] not in LANGUAGE_CODES
                and all(x['score'] >= .8 and x['margin'] >= .2 for x in (previous, current))):
            return {'accepted': False, 'reason': 'unsupported_language'}
        previous = current
    return {'accepted': False, 'reason': 'uncertain_or_short'}


def main():
    connection = Connection(int(sys.argv[1]))
    try:
        import numpy as np
        from faster_whisper import WhisperModel
        from faster_whisper.vad import get_speech_timestamps, VadOptions
        model = WhisperModel(sys.argv[2], device='cpu', compute_type='int8', cpu_threads=8,
                             num_workers=1, local_files_only=True)
        connection.send({'ready': True})
        while True:
            data = connection.recv()
            audio = np.frombuffer(data, dtype='<f4')
            segments = get_speech_timestamps(audio, VadOptions(min_speech_duration_ms=250,
                                              min_silence_duration_ms=300, speech_pad_ms=0))
            connection.send(identify(audio, model, segments))
            del audio, data, segments
    except (EOFError, BrokenPipeError):
        pass
    except Exception:
        try:
            connection.send({'accepted': False, 'reason': 'detector_error'})
        except (OSError, EOFError):
            pass
    finally:
        connection.close()


if __name__ == '__main__':
    main()
