"""One bounded CPU detection attempt per submitted automatic utterance."""
import multiprocessing
import os
from pathlib import Path
import subprocess

# Explicitly map unambiguous language labels. Dialects with no safe mapping abstain.
LANGUAGE_CODES = {
    'de': 'deu', 'en': 'eng', 'tr': 'tur', 'ar': 'arb', 'ru': 'rus', 'uk': 'ukr',
    'pl': 'pol', 'ro': 'ron', 'it': 'ita', 'bg': 'bul', 'hr': 'hrv', 'sr': 'srp',
    'fa': 'pes', 'el': 'ell', 'fr': 'fra', 'es': 'spa', 'pt': 'por', 'nl': 'nld',
    'cs': 'ces', 'sk': 'slk', 'sl': 'slv', 'hu': 'hun', 'sv': 'swe', 'da': 'dan',
    'fi': 'fin', 'et': 'est', 'lv': 'lvs', 'lt': 'lit', 'ja': 'jpn', 'ko': 'kor',
    'zh': 'cmn', 'hi': 'hin', 'ur': 'urd', 'bn': 'ben', 'ta': 'tam', 'te': 'tel',
    'vi': 'vie', 'th': 'tha', 'id': 'ind', 'sw': 'swh', 'he': 'heb', 'af': 'afr',
    'ca': 'cat', 'cy': 'cym', 'eu': 'eus', 'gl': 'glg', 'is': 'isl', 'mk': 'mkd',
    'az': 'azj', 'hy': 'hye', 'ka': 'kat', 'kk': 'kaz', 'ne': 'npi', 'ml': 'mal',
    'mr': 'mar', 'gu': 'guj', 'kn': 'kan', 'pa': 'pan', 'so': 'som', 'yo': 'yor',
}


def accepted_language(previous, current):
    """Full ranking first; two consecutive qualified prefixes, never force a label."""
    if not previous or not current:
        return None
    for item in (previous, current):
        if item['score'] < .8 or item['margin'] < .2:
            return None
    if previous['language'] != current['language']:
        return None
    return LANGUAGE_CODES.get(current['language'])


class LanguageDetector:
    def __init__(self, python, model_path, timeout=30):
        self.python, self.model_path, self.timeout = python, model_path, timeout
        self.process = self.connection = None

    def detect(self, data):
        from .audio import decode_wav
        audio, _ = decode_wav(data)
        if len(audio) < 5 * 16000:
            return {'accepted': False, 'reason': 'insufficient_audio'}
        try:
            if not self.process or self.process.poll() is not None:
                self.close()
                self.connection, child = multiprocessing.Pipe()
                env = dict(os.environ, CUDA_VISIBLE_DEVICES='', OPENBLAS_NUM_THREADS='1',
                           MKL_NUM_THREADS='1', OMP_NUM_THREADS='8')
                self.process = subprocess.Popen(
                    [self.python, '-m', 'backend.lid_worker', str(child.fileno()), self.model_path],
                    pass_fds=(child.fileno(),), env=env, cwd=Path(__file__).resolve().parents[1],
                    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                child.close()
                if not self.connection.poll(self.timeout) or not self.connection.recv().get('ready'):
                    raise TimeoutError()
            self.connection.send(audio.astype('<f4').tobytes())
            if not self.connection.poll(self.timeout):
                raise TimeoutError()
            result = self.connection.recv()
            if result.get('reason') == 'detector_error':
                self.close()
            return result
        except (OSError, EOFError, TimeoutError):
            self.close()
            return {'accepted': False, 'reason': 'detector_unavailable'}

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None
        if self.process:
            if self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=3)
            self.process = None
