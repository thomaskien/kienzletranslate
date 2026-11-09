import unittest
import uuid
from backend.lid import accepted_language, LANGUAGE_CODES
from backend.lid_worker import identify
from backend.process_model import ProcessModel, ModelOperationError
from backend.service import Service, ServiceError
from backend.tests.test_core import FakeModel, wav


class Detector:
    def __init__(self, result): self.result, self.calls = result, 0
    def detect(self, data): self.calls += 1; return self.result
    def close(self): pass


class ResourceTests(unittest.TestCase):
    def setUp(self):
        self.now = 0
        self.model = FakeModel()
        self.detector = Detector({'accepted': True, 'language': 'fra'})
        self.service = Service(self.model, detector=self.detector, clock=lambda:self.now)
    def tearDown(self):
        self.model.release.set()
        self.service.close()
    def test_heartbeat_disconnect_and_multiple_clients(self):
        self.service.heartbeat('a','one',activity=True)
        self.service.queue.join()
        self.now = 80
        self.service.heartbeat('b','two')
        self.now = 100
        self.service.maintenance()
        self.assertEqual(self.model.state,'ready')
        self.now = 171
        self.service.maintenance()
        self.service.queue.join()
        self.assertEqual(self.model.state,'unloaded')
    def test_hidden_page_heartbeats_do_not_extend_gpu_lease(self):
        self.service.heartbeat('a','one',activity=True)
        self.service.queue.join()
        for now in (30,60,91):
            self.now=now
            self.service.heartbeat('a','one',active=False)
        self.service.maintenance()
        self.service.queue.join()
        self.assertEqual(self.model.state,'unloaded')
    def test_idle_heartbeat_does_not_reload_but_activity_does(self):
        self.service.heartbeat('a','one',activity=True)
        self.service.queue.join()
        self.now = 301
        self.service.heartbeat('a','one')
        self.service.maintenance()
        self.service.queue.join()
        self.assertEqual(self.model.state,'unloaded')
        self.service.heartbeat('a','one')
        self.assertEqual(self.model.state,'unloaded')
        self.service.heartbeat('a','one',activity=True)
        self.service.queue.join()
        self.assertEqual(self.model.state,'ready')
    def test_recording_and_queue_protect_model(self):
        self.model.load()
        self.now = 400
        self.service.heartbeat('a','one',recording=True)
        self.service.maintenance()
        self.assertEqual(self.model.state,'ready')
        with self.assertRaises(ServiceError):self.service.lifecycle('unload')
        self.service.heartbeat('a','one',recording=False)
        self.model.release.clear()
        self.service.submit('a',str(uuid.uuid4()),wav(),'deu','eng',False)
        self.assertTrue(self.model.entered.wait(1))
        self.now=1000
        self.service.maintenance()
        self.assertEqual(self.model.state,'ready')
    def test_automatic_success_and_abstention_keep_sessions_separate(self):
        uid=str(uuid.uuid4())
        self.service.submit('a',uid,wav(),'auto','deu',False)
        self.service.queue.join()
        result=self.service.result('a',uid)
        self.assertEqual(result['detection']['language'],'fra')
        self.assertEqual(result['status'],'complete')
        self.assertEqual(self.detector.calls,1)
        with self.assertRaises(ServiceError):self.service.result('b',uid)
        self.detector.result={'accepted':False,'reason':'uncertain'}
        other=str(uuid.uuid4())
        self.service.submit('b',other,wav(),'auto','deu',False)
        self.service.queue.join()
        self.assertEqual(self.service.result('b',other)['status'],'language_required')
        self.assertEqual(self.model.calls,1)
    def test_insufficient_vram_never_starts_gpu_child(self):
        model=ProcessModel('/unused',8192,memory_reader=lambda:4096)
        with self.assertRaises(ModelOperationError) as cm:model.load()
        self.assertEqual(cm.exception.code,'gpu_memory')
        self.assertIsNone(model.process)
        self.assertEqual(model.error_code,'gpu_memory')
    def test_detection_requires_two_strong_results_and_supported_code(self):
        strong={'language':'de','score':.95,'margin':.8}
        self.assertEqual(accepted_language(strong,strong),'deu')
        self.assertIsNone(accepted_language(strong,dict(strong,language='en')))
        self.assertIsNone(accepted_language(strong,dict(strong,score=.79)))
        self.assertIsNone(accepted_language(strong,dict(strong,margin=.19)))
        self.assertIsNone(accepted_language(dict(strong,language='ku'),dict(strong,language='ku')))
        import json
        from pathlib import Path
        supported={x['code'] for x in json.loads(Path('backend/languages.json').read_text())}
        self.assertTrue(set(LANGUAGE_CODES.values())<=supported)
    def test_speech_gate_short_audio_and_prefixes(self):
        class PrefixModel:
            calls=0
            def detect_language(self,**kwargs):
                self.calls+=1
                return 'de',.96,[('de',.96),('en',.02)]
        model=PrefixModel()
        self.assertFalse(identify(range(8*16000),model,[])['accepted'])
        self.assertFalse(identify(range(4*16000),model,[{'start':0,'end':4*16000}])['accepted'])
        result=identify(range(8*16000),model,[{'start':0,'end':8*16000}])
        self.assertTrue(result['accepted'])
        self.assertEqual(result['audio_seconds'],5)
        self.assertEqual(model.calls,3) # one 3s prefix on short input, then 3/5s


if __name__=='__main__':unittest.main()
