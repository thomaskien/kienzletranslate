import io
import struct
import threading
import time
import unittest
import uuid
import wave

from backend.audio import inspect_wav
from backend.service import Service, ServiceError


def wav(seconds=.1, rate=48000):
    stream = io.BytesIO()
    with wave.open(stream, 'wb') as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(rate)
        output.writeframes(b'\0\0' * int(rate*seconds))
    return stream.getvalue()


class FakeModel:
    state = 'unloaded'
    error = None
    def __init__(self):
        self.entered = threading.Event()
        self.release = threading.Event()
        self.release.set()
        self.calls = 0
    def load(self): self.state = 'ready'
    def unload(self): self.state = 'unloaded'
    def translate(self, data, source, target, tts):
        self.load()
        self.calls += 1
        self.entered.set()
        self.release.wait(2)
        return {'original_text':'test', 'translated_text':target, 'audio_available':tts}, b'audio' if tts else None


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.model = FakeModel()
        self.service = Service(self.model)
    def tearDown(self):
        self.model.release.set()
        self.service.close()
    def submit(self, session='a', uid=None):
        uid = uid or str(uuid.uuid4())
        self.service.submit(session,uid,wav(),'deu','eng',True)
        return uid
    def test_wav_boundaries_and_truncation(self):
        pcm, rate, frames = inspect_wav(wav())
        self.assertEqual((rate,frames,len(pcm)),(48000,4800,9600))
        with self.assertRaises(ValueError): inspect_wav(wav()[:-4])
        with self.assertRaises(ValueError): inspect_wav(wav(60.01,8000))
        with self.assertRaises(ValueError): inspect_wav(b'not a wave file')
    def test_sessions_cannot_read_each_others_audio(self):
        uid = self.submit()
        self.service.queue.join()
        self.assertEqual(self.service.result('a',uid,audio=True), b'audio')
        with self.assertRaises(ServiceError): self.service.result('b',uid,audio=True)
        self.service.clear('a')
        with self.assertRaises(ServiceError): self.service.result('a',uid)
    def test_superseded_job_does_not_reappear(self):
        self.model.release.clear()
        old = self.submit()
        self.assertTrue(self.model.entered.wait(1))
        new = self.submit()
        self.model.release.set()
        self.service.queue.join()
        with self.assertRaises(ServiceError): self.service.result('a',old)
        self.assertEqual(self.service.result('a',new)['status'],'complete')
    def test_unload_rejected_during_inference_then_possible(self):
        self.model.release.clear()
        self.submit()
        self.assertTrue(self.model.entered.wait(1))
        with self.assertRaises(ServiceError): self.service.lifecycle('unload')
        self.model.release.set()
        self.service.queue.join()
        self.service.lifecycle('unload')
        self.service.queue.join()
        self.assertEqual(self.service.health()['state'],'unloaded')
    def test_expired_results_removed(self):
        uid = self.submit()
        self.service.queue.join()
        self.service.ttl = -1
        with self.assertRaises(ServiceError): self.service.result('a',uid)
    def test_late_upload_cannot_replace_newer_utterance(self):
        uid=str(uuid.uuid4())
        self.service.submit('a',uid,wav(),'deu','eng',False,200)
        self.service.queue.join()
        with self.assertRaises(ServiceError):
            self.service.submit('a',str(uuid.uuid4()),wav(),'deu','eng',False,100)
        self.assertEqual(self.service.result('a',uid)['status'],'complete')


if __name__ == '__main__': unittest.main()
