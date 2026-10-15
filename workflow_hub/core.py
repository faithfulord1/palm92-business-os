"""Local evidence and approval store. No model can approve or send an action."""
import csv
import hashlib
import io
import json
import re
import sqlite3
import uuid
from datetime import date, datetime, timezone
from pathlib import Path


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def required(value, name, limit=10000):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f'{name} must contain 1 to {limit} characters')
    return value.strip()


from vault import Vault


class Store(Vault):
    def __init__(self, root, password=None):
        super().__init__(root, password)
        with self.connect() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS documents(id TEXT PRIMARY KEY, name TEXT, sha256 TEXT,
              parser TEXT, pages TEXT, created TEXT, case_id TEXT);
            CREATE TABLE IF NOT EXISTS findings(id TEXT PRIMARY KEY, data TEXT);
            CREATE TABLE IF NOT EXISTS actions(id TEXT PRIMARY KEY, data TEXT);
            CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY, at TEXT, kind TEXT,
              entity TEXT, details TEXT, previous TEXT, hash TEXT);
            ''')

    def event(self, db, kind, entity, details):
        last = db.execute('SELECT hash FROM events ORDER BY seq DESC LIMIT 1').fetchone()
        value = dict(at=now(), kind=kind, entity=entity, details=details,
                     previous=last['hash'] if last else '')
        db.execute('INSERT INTO events(at,kind,entity,details,previous,hash) VALUES(?,?,?,?,?,?)',
                   (value['at'], kind, entity, json.dumps(details, sort_keys=True), value['previous'], digest(value)))

    def ingest(self, name, raw, case_id, engine='basic'):
        from adapters import extract
        case_id = required(case_id, 'Case', 100)
        name = Path(required(name, 'Filename', 200)).name
        if len(raw) > 20 * 1024 * 1024:
            raise ValueError('File exceeds 20 MB')
        sha = hashlib.sha256(raw).hexdigest()
        docid = digest([case_id, sha, engine])[:24]
        with self.connect() as db:
            existing = db.execute('SELECT * FROM documents WHERE id=?', (docid,)).fetchone()
        if existing:
            return self.document(docid)
        suffix = Path(name).suffix.lower()
        if suffix not in ('.txt', '.md', '.csv', '.pdf', '.docx', '.png', '.jpg', '.jpeg'):
            raise ValueError('Supported: PDF, DOCX, PNG/JPG, TXT, Markdown and CSV')
        folder = self.root / 'originals'
        folder.mkdir(exist_ok=True, mode=0o700)
        source = folder / (docid + suffix + '.enc')
        source.write_bytes(self.seal(raw, docid.encode()))
        try:
            pages, parser = extract(name, raw, engine)
        except Exception:
            source.unlink(missing_ok=True)
            raise
        if not any(p['text'].strip() for p in pages):
            source.unlink(missing_ok=True)
            raise ValueError('No text extracted. A scanned document needs Docling/OCR. Not indexed.')
        if sum(len(p['text']) for p in pages) > 2_000_000:
            source.unlink(missing_ok=True)
            raise ValueError('Extracted text exceeds 2 million characters; split the document')
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('INSERT OR IGNORE INTO documents VALUES(?,?,?,?,?,?,?)',
                       (docid, name, sha, parser, json.dumps(pages), now(), case_id))
            self.event(db, 'document_ingested', docid, {'sha256': sha, 'parser': parser, 'case': case_id})
        return self.document(docid)

    def document(self, docid):
        with self.connect() as db:
            row = db.execute('SELECT * FROM documents WHERE id=?', (docid,)).fetchone()
        if not row:
            raise ValueError('Document not found')
        result = dict(row)
        result['pages'] = json.loads(result['pages'])
        return result

    def search(self, case_id, query):
        terms = set(re.findall(r'\w+', required(query, 'Query').lower()))
        hits = []
        with self.connect() as db:
            docs = db.execute('SELECT * FROM documents WHERE case_id=?', (case_id,)).fetchall()
        for row in docs:
            for page in json.loads(row['pages']):
                for paragraph in re.split(r'\n\s*\n', page['text']):
                    score = sum(t in paragraph.lower() for t in terms)
                    if score:
                        hits.append(dict(document_id=row['id'], source=row['name'], page=page['page'],
                                         quote=paragraph[:3000], score=score, sha256=row['sha256']))
        return sorted(hits, key=lambda x: x['score'], reverse=True)[:12]

    def finding(self, data):
        doc = self.document(data['document_id'])
        quote = required(data['quote'], 'Exact quote', 10000)
        page_no = int(data['page'])
        page = next((p for p in doc['pages'] if p['page'] == page_no), None)
        if not page or quote not in page['text']:
            raise ValueError('Quote must occur exactly on the selected extracted page')
        if data['status'] not in ('CLAIM_ONLY', 'GAP', 'CONFLICT', 'VERIFIED', 'NOT_APPLICABLE'):
            raise ValueError('Invalid evidence status')
        item = dict(id=uuid.uuid4().hex, document_id=doc['id'], case_id=doc['case_id'],
                    source=doc['name'], sha256=doc['sha256'], page=page_no, quote=quote,
                    control=required(data['control'], 'Control', 200), status=data['status'],
                    note=required(data['note'], 'Reviewer rationale'),
                    reviewer=required(data['reviewer'], 'Reviewer', 100), created=now())
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('INSERT INTO findings VALUES(?,?)', (item['id'], json.dumps(item)))
            self.event(db, 'finding_recorded', item['id'], {'status': item['status'], 'document': doc['id'], 'reviewer': item['reviewer']})
        return item

    def assess(self, data):
        """Deliberately tri-state: unknown facts cannot silently become low risk."""
        checks = [('mfa', 'TPRM-IAM-001', 'MFA evidence'),
                  ('encryption', 'TPRM-ENC-001', 'Encryption evidence'),
                  ('recovery_test', 'TPRM-RES-001', 'Recovery test evidence'),
                  ('independent_assurance', 'TPRM-ASS-001', 'Independent assurance')]
        findings = []
        for field, control, label in checks:
            value = data.get(field)
            if value is not None and type(value) is not bool:
                raise ValueError(f'{field} must be true, false or null')
            findings.append(dict(control=control, topic=label,
                                 status='CLAIM_ONLY' if value is True else 'GAP' if value is False else 'UNKNOWN',
                                 next_action='Verify supporting evidence' if value is True else 'Request evidence and reviewer assessment'))
        expiry = data.get('certificate_expiry')
        if expiry:
            exp = date.fromisoformat(expiry)
            findings.append(dict(control='TPRM-CERT-001', topic='Certificate validity',
                                 status='EXPIRED' if exp < date.today() else 'CLAIM_ONLY',
                                 next_action='Verify issuer, scope and dates independently'))
        return dict(vendor=required(data['vendor'], 'Vendor', 200), findings=findings,
                    decision='HUMAN_REVIEW_REQUIRED', risk_rating='NOT_ASSIGNED',
                    warning='Questionnaire triage only. Claims are not proof of effective controls.')

    def draft(self, data):
        channel = data['channel']
        if channel not in ('linkedin', 'whatsapp', 'github', 'media', 'asana'):
            raise ValueError('Unknown channel')
        item = dict(id=uuid.uuid4().hex, channel=channel,
                    destination=required(data['destination'], 'Destination', 200),
                    text=required(data['text'], 'Draft', 15000), state='DRAFT',
                    public_ready=data.get('public_ready') is True, created=now(), revision=1)
        item['content_hash'] = digest({k: item[k] for k in ('channel', 'destination', 'text', 'public_ready', 'revision')})
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('INSERT INTO actions VALUES(?,?)', (item['id'], json.dumps(item)))
            self.event(db, 'draft_created', item['id'], {'channel': channel, 'content_hash': item['content_hash']})
        return item

    def action(self, action_id):
        with self.connect() as db:
            row = db.execute('SELECT data FROM actions WHERE id=?', (action_id,)).fetchone()
        if not row:
            raise ValueError('Draft not found')
        return json.loads(row['data'])

    def approve(self, action_id, reviewer, expected_hash):
        reviewer = required(reviewer, 'Reviewer', 100)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT data FROM actions WHERE id=?', (action_id,)).fetchone()
            if not row:
                raise ValueError('Draft not found')
            item = json.loads(row['data'])
            if item['state'] != 'DRAFT' or item['content_hash'] != expected_hash:
                raise ValueError('Draft changed or was already reviewed. Refresh first.')
            if item['channel'] == 'linkedin' and not item['public_ready']:
                raise ValueError('LinkedIn requires an explicit public-safe content declaration')
            item.update(state='APPROVED_FOR_EXPORT', reviewer=reviewer, reviewed=now())
            db.execute('UPDATE actions SET data=? WHERE id=?', (json.dumps(item), action_id))
            self.event(db, 'draft_approved', action_id, {'reviewer': reviewer, 'content_hash': expected_hash})
        return item

    def export_action(self, action_id):
        item = self.action(action_id)
        if item['state'] != 'APPROVED_FOR_EXPORT':
            raise ValueError('Human approval required before export')
        from adapters import channel_payload
        payload = channel_payload(item)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            self.event(db, 'approved_draft_exported', action_id, {'content_hash': item['content_hash']})
        return {'action': item, 'payload': payload, 'delivery_status': 'NOT_SENT'}

    def snapshot(self):
        with self.connect() as db:
            documents = [dict(r) for r in db.execute('SELECT id,name,sha256,parser,created,case_id FROM documents ORDER BY created DESC')]
            findings = [json.loads(r['data']) for r in db.execute('SELECT data FROM findings')]
            actions = [json.loads(r['data']) for r in db.execute('SELECT data FROM actions')]
        return dict(documents=documents, findings=findings, actions=actions)

    def audit(self):
        with self.connect() as db:
            events = [dict(r) for r in db.execute('SELECT * FROM events ORDER BY seq')]
        previous = ''
        valid = True
        for e in events:
            value = {k: e[k] for k in ('at', 'kind', 'entity', 'previous')}
            value['details'] = json.loads(e['details'])
            valid &= e['previous'] == previous and e['hash'] == digest(value)
            previous = e['hash']
        return {'valid': valid, 'events': events, 'head_hash': previous,
                'boundary': 'Local hash chain detects changes against a trusted checkpoint; it is not immutable storage.'}

    def evidence_export(self, case_id):
        snap = self.snapshot()
        findings = [f for f in snap['findings'] if f['case_id'] == case_id]
        out = io.StringIO(newline='')
        fields = ['id','control','status','source','page','quote','note','reviewer','created','sha256']
        writer = csv.DictWriter(out, fields, extrasaction='ignore')
        writer.writeheader()
        for row in findings:
            # Prevent spreadsheet formula execution when users open the register.
            writer.writerow({k: "'"+str(v) if str(v).lstrip().startswith(('=', '+', '-', '@')) else v for k,v in row.items()})
        corpus = []
        for doc in snap['documents']:
            if doc['case_id'] != case_id:
                continue
            full = self.document(doc['id'])
            corpus.append(f"# {doc['name']}\nSource SHA-256: {doc['sha256']}\n")
            corpus.extend(f"## Page {p['page']}\n{p['text']}\n" for p in full['pages'])
        return {'case_id': case_id, 'register_csv': out.getvalue(), 'knowledge_markdown': '\n'.join(corpus),
                'findings': findings, 'audit_checkpoint': self.audit()['head_hash']}
