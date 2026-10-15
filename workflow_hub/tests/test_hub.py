import base64
import hashlib
import hmac
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from core import Store
import adapters
import privacy
import delivery
import analyst
from server import make_handler
from http.server import ThreadingHTTPServer
import urllib.request
import urllib.error

PASS='test-only-strong-passphrase'

class HubTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.s=Store(self.tmp.name,PASS)
  self.doc=self.s.ingest('private.md',b'Name: Fictional Alice\nEmail: alice@example.test\n\nMFA is enabled.\n\nNo recovery evidence.', 'CLIENT-A')
 def tearDown(self): self.tmp.cleanup()
 def draft(self,channel='linkedin',public=True):
  return self.s.draft({'channel':channel,'destination':'urn:li:person:example' if channel=='linkedin' else '+447700900123','text':'Fictional test message','public_ready':public})
 def approved(self,channel='linkedin'):
  a=self.draft(channel);return self.s.approve(a['id'],'Test reviewer',a['content_hash'])
 def test_at_rest_contains_no_plaintext(self):
  for path in Path(self.tmp.name).rglob('*'):
   if path.is_file():
    raw=path.read_bytes();self.assertNotIn(b'Fictional Alice',raw);self.assertNotIn(b'alice@example.test',raw);self.assertNotIn(b'SQLite format',raw)
 def test_wrong_password_fails(self):
  with self.assertRaises(ValueError):Store(self.tmp.name,'wrong-password-value')
 def test_restart_recovers_encrypted_data(self):
  other=Store(self.tmp.name,PASS);self.assertEqual(other.document(self.doc['id'])['name'],'private.md')
 def test_tampered_vault_fails(self):
  p=Path(self.tmp.name)/'database.vault';raw=bytearray(p.read_bytes());raw[-1]^=1;p.write_bytes(raw)
  with self.assertRaises(ValueError):Store(self.tmp.name,PASS)
 def test_duplicate_ingest_is_idempotent(self):
  second=self.s.ingest('again.md',b'Name: Fictional Alice\nEmail: alice@example.test\n\nMFA is enabled.\n\nNo recovery evidence.','CLIENT-A')
  self.assertEqual(second['id'],self.doc['id']);self.assertEqual(len(self.s.snapshot()['documents']),1)
 def test_cases_do_not_mix(self):
  self.assertEqual(self.s.search('OTHER','MFA'),[])
 def test_search_preserves_source(self):
  h=self.s.search('CLIENT-A','MFA')[0];self.assertEqual(h['page'],1);self.assertEqual(h['sha256'],self.doc['sha256'])
 def test_invented_quote_rejected(self):
  with self.assertRaises(ValueError):self.s.finding(dict(document_id=self.doc['id'],page=1,quote='invented',status='VERIFIED'))
 def test_wrong_page_rejected(self):
  with self.assertRaises(ValueError):self.s.finding(dict(document_id=self.doc['id'],page=2,quote='MFA is enabled.',status='VERIFIED'))
 def test_unknown_not_low_risk(self):
  r=self.s.assess({'vendor':'Fictional'});self.assertTrue(all(f['status']=='UNKNOWN' for f in r['findings']));self.assertEqual(r['risk_rating'],'NOT_ASSIGNED')
 def test_string_boolean_rejected(self):
  with self.assertRaises(ValueError):self.s.assess({'vendor':'Test','mfa':'false'})
 def test_claims_not_verified(self):
  self.assertEqual(self.s.assess({'vendor':'Test','mfa':True})['findings'][0]['status'],'CLAIM_ONLY')
 def test_unapproved_export_blocked(self):
  with self.assertRaises(ValueError):self.s.export_action(self.draft()['id'])
 def test_private_linkedin_blocked(self):
  a=self.draft(public=False)
  with self.assertRaises(ValueError):self.s.approve(a['id'],'Reviewer',a['content_hash'])
 def test_stale_approval_blocked(self):
  a=self.draft()
  with self.assertRaises(ValueError):self.s.approve(a['id'],'Reviewer','wrong-hash')
 def test_approved_export_does_not_send(self):
  r=self.s.export_action(self.approved()['id']);self.assertEqual(r['delivery_status'],'NOT_SENT')
 def test_audit_chain_and_tamper_detection(self):
  self.assertTrue(self.s.audit()['valid'])
  with self.s.connect() as db:db.execute("UPDATE events SET kind='changed' WHERE seq=1")
  self.assertFalse(self.s.audit()['valid'])
 def test_redaction_preview_removes_identifiers(self):
  r=privacy.preview(self.doc,['recovery']);text=r['pages'][0]['text'];self.assertNotIn('Alice',text);self.assertNotIn('alice@example.test',text);self.assertNotIn('recovery',text)
 def test_redaction_requires_review(self):
  r=privacy.preview(self.doc,[])
  with self.assertRaises(ValueError):privacy.approve_redaction(self.s,self.doc['id'],[],r['preview_hash'],'Reviewer','Test',False)
 def test_redaction_changed_terms_blocked(self):
  r=privacy.preview(self.doc,[])
  with self.assertRaises(ValueError):privacy.approve_redaction(self.s,self.doc['id'],['MFA'],r['preview_hash'],'Reviewer','Test',True)
 def test_redacted_pdf_has_no_original_identifiers(self):
  from pypdf import PdfReader
  r=privacy.preview(self.doc,[]);a=privacy.approve_redaction(self.s,self.doc['id'],[],r['preview_hash'],'Reviewer','Fictional test',True)
  raw=privacy.export_redaction(self.s,a['id']);pdf=PdfReader(io.BytesIO(raw));text=''.join(p.extract_text() for p in pdf.pages)
  self.assertNotIn('Alice',text);self.assertNotIn('alice@example.test',text);self.assertIn('MFA is enabled.',text);self.assertFalse(pdf.attachments)
 def test_pdf_page_provenance(self):
  from reportlab.pdfgen import canvas
  b=io.BytesIO();c=canvas.Canvas(b);c.drawString(40,700,'First page');c.showPage();c.drawString(40,700,'Second page');c.save()
  d=self.s.ingest('two.pdf',b.getvalue(),'PAGES');self.assertIn('Second page',d['pages'][1]['text']);self.assertEqual(d['pages'][1]['page'],2)
 def test_scanned_pdf_not_silently_accepted(self):
  from pypdf import PdfWriter
  w=PdfWriter();w.add_blank_page(100,100);b=io.BytesIO();w.write(b)
  with self.assertRaises(ValueError):self.s.ingest('blank.pdf',b.getvalue(),'SCAN')
 def test_csv_formula_neutralised(self):
  self.s.finding(dict(document_id=self.doc['id'],page=1,quote='MFA is enabled.',control='=DANGER()',status='CLAIM_ONLY',note='Checked',reviewer='Tester'))
  self.assertIn("'=DANGER()",self.s.evidence_export('CLIENT-A')['register_csv'])
 def test_guidance_does_not_claim_pass(self):
  r=analyst.guidance(self.s,'CLIENT-A','supplier-onboarding');self.assertEqual(r['decision'],'HUMAN_REVIEW_REQUIRED');self.assertEqual(len(r['next_steps']),6)
 def test_live_send_off_by_default(self):
  a=self.approved()
  with patch.dict(os.environ,{},clear=True):
   with self.assertRaises(ValueError):delivery.send(self.s,a['id'],a['content_hash'])
 def test_send_once_and_receipt(self):
  a=self.approved();calls=[]
  def fake(*args):calls.append(args);return {'status':201,'headers':{'x-restli-id':'urn:li:share:TEST'},'body':{}}
  with patch.dict(os.environ,{'PALM92_ALLOW_CLOUD_CONNECTORS':'YES','PALM92_ENABLE_LIVE_SEND':'YES','PALM92_LINKEDIN_TOKEN':'fake','PALM92_LINKEDIN_VERSION':'202610'}):
   self.assertEqual(delivery.send(self.s,a['id'],a['content_hash'],http=fake)['state'],'SENT')
   with self.assertRaises(ValueError):delivery.send(self.s,a['id'],a['content_hash'],http=fake)
  self.assertEqual(len(calls),1)
 def test_uncertain_delivery_never_retries(self):
  a=self.approved()
  def failed(*args):raise TimeoutError()
  with patch.dict(os.environ,{'PALM92_ALLOW_CLOUD_CONNECTORS':'YES','PALM92_ENABLE_LIVE_SEND':'YES','PALM92_LINKEDIN_TOKEN':'fake','PALM92_LINKEDIN_VERSION':'202610'}):
   self.assertEqual(delivery.send(self.s,a['id'],a['content_hash'],http=failed)['state'],'DELIVERY_UNCERTAIN')
   with self.assertRaises(ValueError):delivery.send(self.s,a['id'],a['content_hash'],http=failed)
 def test_whatsapp_signature_and_deduplication(self):
  raw=json.dumps({'entry':[{'changes':[{'value':{'metadata':{'phone_number_id':'123'},'messages':[{'id':'unique','from':'447700900123','timestamp':str(int(datetime.now(timezone.utc).timestamp())),'type':'text','text':{'body':'Hello'}}]}}]}]}).encode()
  sig='sha256='+hmac.new(b'testsecret',raw,hashlib.sha256).hexdigest()
  with patch.dict(os.environ,{'PALM92_META_APP_SECRET':'testsecret','PALM92_WHATSAPP_PHONE_ID':'123'}):
   with self.assertRaises(ValueError):delivery.receive_whatsapp(self.s,raw,'invalid')
   self.assertEqual(delivery.receive_whatsapp(self.s,raw,sig)['new_messages'],1)
   self.assertEqual(delivery.receive_whatsapp(self.s,raw,sig)['new_messages'],0)
 def test_whatsapp_outside_window_blocked(self):
  a=self.approved('whatsapp')
  with patch.dict(os.environ,{'PALM92_ALLOW_CLOUD_CONNECTORS':'YES','PALM92_ENABLE_LIVE_SEND':'YES','PALM92_WHATSAPP_TOKEN':'fake','PALM92_WHATSAPP_PHONE_ID':'123','PALM92_META_VERSION':'v23.0'}):
   with self.assertRaises(ValueError):delivery.send(self.s,a['id'],a['content_hash'],consent=True)
 def test_local_endpoint_rejects_external_hosts(self):
  with self.assertRaises(ValueError):adapters.request_json('http://example.com',local=True)
 def test_offline_default_blocks_github(self):
  with patch.dict(os.environ,{},clear=True):
   with self.assertRaises(ValueError):adapters.github_status('faithfulord1/palm92-business-os')
 def test_cloud_model_rejected(self):
  with patch.dict(os.environ,{'PALM92_MODEL':'test:cloud'}),patch.object(adapters,'request_json',return_value={'models':[{'name':'test:cloud'}]}):
   with self.assertRaises(ValueError):adapters.local_draft('test')
 def test_local_model_adapter(self):
  with patch.dict(os.environ,{'PALM92_MODEL':'test:local'}),patch.object(adapters,'request_json',side_effect=[{'models':[{'name':'test:local'}]},{'message':{'content':'Draft only'}}]):
   self.assertEqual(adapters.local_draft('test')['state'],'UNREVIEWED_DRAFT')
 def test_media_graph_is_export_only(self):
  graph=adapters.media_workflow('navy and amber','installed.safetensors');self.assertEqual(graph['7']['class_type'],'SaveImage')

class HTTPTests(unittest.TestCase):
 def setUp(self):
  import time
  self.tmp=tempfile.TemporaryDirectory();self.s=Store(self.tmp.name,PASS)
  self.server=ThreadingHTTPServer(('127.0.0.1',0),make_handler(self.s,'test-token',0));self.port=self.server.server_port
  self.server.RequestHandlerClass=make_handler(self.s,'test-token',self.port);self.server.last_activity=time.monotonic()
  self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
 def tearDown(self):self.server.shutdown();self.server.server_close();self.thread.join();self.tmp.cleanup()
 def request(self,path,headers=None,data=None):
  r=urllib.request.Request(f'http://127.0.0.1:{self.port}'+path,headers=headers or {},data=json.dumps(data).encode() if data is not None else None)
  return urllib.request.urlopen(r)
 def test_no_auth_denied(self):
  with self.assertRaises(urllib.error.HTTPError) as ctx:self.request('/api/state')
  self.assertEqual(ctx.exception.code,401)
 def test_cross_origin_denied(self):
  with self.assertRaises(urllib.error.HTTPError) as ctx:self.request('/api/state',{'Authorization':'Bearer test-token','Origin':'https://evil.example'})
  self.assertEqual(ctx.exception.code,403)
 def test_dashboard_and_state(self):
  with self.request('/') as r:self.assertIn(b'Privacy & redaction',r.read())
  with self.request('/api/state',{'Authorization':'Bearer test-token'}) as r:self.assertEqual(json.load(r)['capabilities']['storage'],'PASSWORD ENCRYPTED')
 def test_import_search_roundtrip(self):
  headers={'Authorization':'Bearer test-token','Content-Type':'application/json'}
  with self.request('/api/ingest',headers,{'name':'test.txt','base64':base64.b64encode(b'MFA evidence').decode(),'case_id':'TEST'}) as r:self.assertEqual(r.status,200)
  with self.request('/api/search',headers,{'query':'MFA','case_id':'TEST'}) as r:self.assertEqual(len(json.load(r)),1)

if __name__=='__main__':unittest.main()
