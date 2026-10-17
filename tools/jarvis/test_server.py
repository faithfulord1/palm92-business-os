"""Offline regression checks. No account access, network, or model required."""
import io
import unittest
from unittest.mock import patch
import local_server


class ServerTests(unittest.TestCase):
    def handler(self, path='/api/brain', body=None, origin='http://127.0.0.1:4700', host='127.0.0.1:4700'):
        h = object.__new__(local_server.Handler)
        h.path = path
        raw = body if body is not None else b''
        h.headers = {'Host': host, 'Origin': origin, 'Content-Length': str(len(raw))}
        h.rfile = io.BytesIO(raw)
        h.reply = lambda status, obj: (status, obj)
        return h

    def test_models_are_reported(self):
        with patch.object(local_server, 'ollama', return_value={'models': [{'name': 'qwen3:0.6b'}]}):
            code, data = self.handler().do_GET()
        self.assertEqual(code, 200)
        self.assertEqual(data['models'], ['qwen3:0.6b'])

    def test_offline_brain_is_explicit(self):
        with patch.object(local_server, 'ollama', side_effect=OSError('offline')):
            code, data = self.handler().do_GET()
        self.assertEqual(code, 503)
        self.assertFalse(data['ready'])

    def test_foreign_origin_never_calls_model(self):
        with patch.object(local_server, 'ollama') as model:
            code, _ = self.handler('/api/chat', b'{}', origin='https://other.example').do_POST()
        self.assertEqual(code, 403)
        model.assert_not_called()

    def test_rebinding_host_is_rejected(self):
        code, _ = self.handler(host='other.example:4700').do_GET()
        self.assertEqual(code, 403)

    def test_chat_uses_local_model_without_action_claims(self):
        results = [{'models': [{'name': 'qwen3:0.6b'}]}, {'message': {'content': 'Here is a draft.'}}]
        with patch.object(local_server, 'ollama', side_effect=results) as model:
            code, data = self.handler('/api/chat', b'{"question":"Draft a reply","notes":[]}').do_POST()
        self.assertEqual(code, 200)
        self.assertEqual(data['answer'], 'Here is a draft.')
        self.assertIn('NO action tools', model.call_args.args[1]['messages'][0]['content'])

    def test_blank_question_never_calls_model(self):
        with patch.object(local_server, 'ollama') as model:
            code, _ = self.handler('/api/chat', b'{"question":" "}').do_POST()
        self.assertEqual(code, 400)
        model.assert_not_called()


if __name__ == '__main__':
    unittest.main()
