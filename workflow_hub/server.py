"""Single-user local dashboard. Bind only to loopback; never deploy publicly."""
import base64
import binascii
import json
import os
import secrets
import threading
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from core import Store
import adapters

UI = Path(__file__).with_name('dashboard.html')


def make_handler(store, token, port):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass  # Do not log source content, URLs, or auth tokens.

        def reply(self, status, data, mime='application/json'):
            raw = json.dumps(data).encode() if mime == 'application/json' else data.encode()
            self.send_response(status)
            self.send_header('Content-Type',mime+'; charset=utf-8')
            self.send_header('Content-Length',str(len(raw)))
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('X-Frame-Options','DENY')
            self.send_header('Referrer-Policy','no-referrer')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
            self.end_headers()
            self.wfile.write(raw)

        def authorised(self):
            if time.monotonic() - self.server.last_activity > 900:
                self.reply(401, {'error':'Workspace locked after inactivity. Restart to unlock.'})
                threading.Thread(target=self.server.shutdown, daemon=True).start()
                return False
            if self.headers.get('Host') not in (f'127.0.0.1:{port}',f'localhost:{port}'):
                self.reply(403,{'error':'Invalid host'})
                return False
            origin = self.headers.get('Origin')
            if origin and origin not in (f'http://127.0.0.1:{port}',f'http://localhost:{port}'):
                self.reply(403,{'error':'Cross-origin access refused'})
                return False
            supplied = self.headers.get('Authorization','')
            if not secrets.compare_digest(supplied,'Bearer '+token):
                self.reply(401,{'error':'Open the private dashboard link printed by the launcher'})
                return False
            self.server.last_activity = time.monotonic()
            return True

        def do_GET(self):
            if self.path == '/':
                if self.headers.get('Host') not in (f'127.0.0.1:{port}',f'localhost:{port}'):
                    return self.reply(403,{'error':'Invalid host'})
                return self.reply(200,UI.read_text(),'text/html')
            if not self.authorised():
                return
            parts = urllib.parse.urlsplit(self.path)
            query = urllib.parse.parse_qs(parts.query)
            try:
                if parts.path == '/api/state':
                    return self.reply(200,{**store.snapshot(),'capabilities':adapters.capabilities()})
                if parts.path == '/api/audit':
                    return self.reply(200,store.audit())
                if parts.path == '/api/document':
                    return self.reply(200,store.document(query['id'][0]))
                if parts.path == '/api/export':
                    return self.reply(200,store.evidence_export(query['case'][0]))
                self.reply(404,{'error':'Not found'})
            except (ValueError,KeyError) as exc:
                self.reply(400,{'error':str(exc)})

        def do_POST(self):
            if not self.authorised():
                return
            try:
                length = int(self.headers.get('Content-Length','0'))
                if not 0 < length <= 29_000_000:
                    return self.reply(413,{'error':'Request size exceeds limit'})
                if self.headers.get('Content-Type','').split(';')[0] != 'application/json':
                    return self.reply(415,{'error':'JSON required'})
                data = json.loads(self.rfile.read(length))
                if not isinstance(data,dict):
                    raise ValueError('Expected an object')
                import privacy
                import analyst
                if self.path == '/api/lock':
                    self.reply(200, {'locked':True})
                    threading.Thread(target=self.server.shutdown, daemon=True).start()
                    return
                routes = {
                    '/api/analyst':lambda:analyst.guidance(store,data['case_id'],data['task']),
                    '/api/privacy-preview':lambda:privacy.preview(store.document(data['document_id']),data.get('manual_terms',[])),
                    '/api/privacy-approve':lambda:privacy.approve_redaction(store,data['document_id'],data.get('manual_terms',[]),data['preview_hash'],data['reviewer'],data['rationale'],data.get('reviewed_all_pages')),
                    '/api/privacy-export':lambda:{'base64':base64.b64encode(privacy.export_redaction(store,data['id'])).decode(),'filename':'redacted-working-copy.pdf'},
                    '/api/ingest':lambda:store.ingest(data['name'],base64.b64decode(data['base64'],validate=True),data['case_id'],data.get('engine','basic')),
                    '/api/search':lambda:store.search(data['case_id'],data['query']),
                    '/api/finding':lambda:store.finding(data),
                    '/api/assess':lambda:store.assess(data),
                    '/api/draft':lambda:store.draft(data),
                    '/api/approve':lambda:store.approve(data['id'],data['reviewer'],data['content_hash']),
                    '/api/export-action':lambda:store.export_action(data['id']),
                    '/api/ai':lambda:adapters.local_draft(data['prompt'],data.get('provider','ollama')),
                    '/api/github':lambda:adapters.github_status(data['repo']),
                    '/api/media':lambda:adapters.media_workflow(data['prompt'],data['checkpoint']),
                }
                if self.path not in routes:
                    return self.reply(404,{'error':'Not found'})
                self.reply(200,routes[self.path]())
            except (ValueError,KeyError,TypeError,binascii.Error) as exc:
                self.reply(400,{'error':str(exc)})
            except Exception:
                self.reply(502,{'error':'The local connector failed. Check installation, model availability, permissions or connectivity. No completion is claimed.'})
    return Handler


def serve(root, port=8792, store=None, open_browser=False):
    token = secrets.token_urlsafe(32)
    server = ThreadingHTTPServer(('127.0.0.1',port),make_handler(store or Store(root),token,port))
    server.last_activity = time.monotonic()
    def idle_lock():
        while True:
            time.sleep(15)
            if time.monotonic() - server.last_activity > 900:
                server.shutdown()
                return
    threading.Thread(target=idle_lock, daemon=True).start()
    print(f'Palm92 local dashboard: http://127.0.0.1:{port}/#{token}',flush=True)
    print('Single-user local mode. Keep this private link to yourself. Ctrl+C to stop.',flush=True)
    if open_browser:
        import webbrowser
        webbrowser.open(f'http://127.0.0.1:{port}/#{token}')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
