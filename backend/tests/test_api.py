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


if __name__ == '__main__': unittest.main()
