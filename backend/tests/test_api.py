import unittest
import uuid
from fastapi.testclient import TestClient
from backend.app import create_app
from backend.tests.test_core import FakeModel, wav


class ApiTests(unittest.TestCase):
    def test_auth_validation_and_isolation(self):
        app = create_app({'backend_token':'t'*64}, FakeModel())
        with TestClient(app) as client:
            self.assertEqual(client.get('/health').status_code,401)
            client.headers['Authorization'] = 'Bearer '+'t'*64
            uid = str(uuid.uuid4())
            path = '/sessions/'+'a'*32+'/utterances'
            params = dict(utterance_id=uid,source_lang='deu',target_lang='eng',speaker_side='bottom',tts=True)
            self.assertEqual(client.post(path,params=params,content=b'garbage').status_code,400)
            response=client.post(path,params=params,content=wav())
            self.assertEqual(response.status_code,202)
            app.state.service.queue.join()
            result=client.get(path+'/'+uid)
            self.assertEqual(result.json()['translated_text'],'eng')
            self.assertEqual(result.headers['cache-control'],'no-store')
            self.assertEqual(client.get('/sessions/'+'b'*32+'/audio/'+uid).status_code,404)
            self.assertEqual(client.delete('/sessions/'+'a'*32).status_code,200)
            self.assertEqual(client.get(path+'/'+uid).status_code,404)

    def test_heartbeat_validation_and_recording_guard(self):
        app=create_app({'backend_token':'t'*64},FakeModel())
        with TestClient(app) as client:
            path='/sessions/'+'a'*32+'/heartbeat'
            data={'client':'b'*32,'active':True,'activity':True,'recording':False}
            self.assertEqual(client.post(path,json=data).status_code,401)
            client.headers['Authorization']='Bearer '+'t'*64
            self.assertEqual(client.post(path,json=dict(data,recording='yes')).status_code,400)
            self.assertEqual(client.post(path,content=b'x'*1025).status_code,413)
            self.assertEqual(client.post(path,json=data).status_code,200)
            app.state.service.queue.join()
            self.assertEqual(client.get('/health').json()['state'],'ready')
            client.post(path,json=dict(data,activity=False,recording=True))
            self.assertEqual(client.post('/model/unload').status_code,409)
            params=dict(utterance_id=str(uuid.uuid4()),source_lang='auto',target_lang='eng',speaker_side='bottom')
            self.assertEqual(client.post('/sessions/'+'a'*32+'/utterances',params=params,content=wav()).status_code,400)


if __name__ == '__main__': unittest.main()
