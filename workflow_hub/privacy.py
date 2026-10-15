"""Local candidate detection and fresh text-only redacted derivatives.
Detection assists a human; it does not certify anonymisation.
"""
import hashlib
import io
import json
import re
import uuid
from core import now, required, digest

PATTERNS = {
    'EMAIL':r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b',
    'PHONE':r'(?<!\w)(?:\+\d[\d ()-]{8,}\d|0\d[\d ()-]{8,}\d)(?!\w)',
    'UK_NI':r'\b[A-CEGHJ-PR-TW-Z][A-CEGHJ-NPR-TW-Z]\s?\d{2}\s?\d{2}\s?\d{2}\s?[A-D]\b',
    'POSTCODE':r'\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b',
    'LONG_NUMBER':r'(?<!\d)(?:\d[ -]?){9,19}(?!\d)',
    'LABELLED_IDENTITY':r'(?im)^(?:full name|name|patient|client|date of birth|dob|address|passport|account number|sort code)\s*[:=]\s*[^\n]+',
}


def preview(document, manual_terms):
    if not isinstance(manual_terms,list) or any(not isinstance(t,str) for t in manual_terms):
        raise ValueError('Manual terms must be a list of strings')
    terms = [t.strip() for t in manual_terms if t.strip()]
    if len(terms)>100 or any(len(t)>300 for t in terms):
        raise ValueError('Maximum 100 manual terms, 300 characters each')
    pages=[]; detections=[]
    for page in document['pages']:
        text=page['text']; spans=[]
        for kind,pattern in PATTERNS.items():
            spans.extend((m.start(),m.end(),kind) for m in re.finditer(pattern,text,re.I))
        for term in terms:
            spans.extend((m.start(),m.end(),'MANUAL') for m in re.finditer(re.escape(term),text,re.I))
        # Merge intersecting spans to avoid leaking fragments when patterns overlap.
        merged=[]
        for start,end,kind in sorted(spans):
            if merged and start <= merged[-1][1]:
                merged[-1]=(merged[-1][0],max(end,merged[-1][1]),merged[-1][2]+'+'+kind)
            else:
                merged.append((start,end,kind))
        cleaned=text
        for start,end,kind in reversed(merged):
            cleaned=cleaned[:start]+'[REDACTED]'+cleaned[end:]
        pages.append({'page':page['page'],'text':cleaned})
        detections.extend({'page':page['page'],'category':kind,'value':text[start:end]} for start,end,kind in merged)
    result={'document_id':document['id'],'source_sha256':document['sha256'],'pages':pages,'detections':detections,
            'manual_terms':terms,'status':'REVIEW_REQUIRED',
            'limitations':'Names, indirect identifiers, health facts and context may remain. Original images, signatures, attachments and metadata are omitted from the fresh derivative, not analysed. Inspect every page. This is not an anonymisation certificate.'}
    result['preview_hash']=digest(result)
    return result


def approve_redaction(store, document_id, terms, expected_hash, reviewer, rationale, reviewed_all_pages):
    if reviewed_all_pages is not True:
        raise ValueError('Review every page and the detection limitations before approval')
    result=preview(store.document(document_id),terms)
    if result['preview_hash'] != expected_hash:
        raise ValueError('Preview changed. Review the new version before approval.')
    result.update(id=uuid.uuid4().hex,reviewer=required(reviewer,'Reviewer',100),
                  rationale=required(rationale,'Purpose and redaction rationale'),reviewed_at=now(),status='REVIEWED_DERIVATIVE')
    with store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        db.execute('CREATE TABLE IF NOT EXISTS redactions(id TEXT PRIMARY KEY,data TEXT)')
        db.execute('INSERT INTO redactions VALUES(?,?)',(result['id'],json.dumps(result)))
        store.event(db,'redaction_reviewed',result['id'],{'source_id':document_id,'reviewer':result['reviewer'],'preview_hash':expected_hash})
    return {'id':result['id'],'status':result['status'],'reviewed_at':result['reviewed_at']}


def export_redaction(store, redaction_id):
    with store.connect() as db:
        row=db.execute('SELECT data FROM redactions WHERE id=?',(redaction_id,)).fetchone()
        if not row:
            raise ValueError('Reviewed redaction not found')
        item=json.loads(row['data'])
    # Construct a new PDF; never copy original PDF streams, metadata or attachments.
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    import textwrap
    out=io.BytesIO();c=canvas.Canvas(out,pagesize=A4,pageCompression=1)
    c.setTitle('Reviewed redacted working copy');c.setAuthor('')
    for page in item['pages']:
        c.setFont('Helvetica',10);y=800
        c.drawString(42,y,f"Redacted working copy | Source page {page['page']}");y-=28
        for line in page['text'].splitlines():
            for wrapped in textwrap.wrap(line,width=95,replace_whitespace=False) or ['']:
                if y<42:
                    c.showPage();c.setFont('Helvetica',10);y=800
                # Unsupported characters are rejected, never silently replaced.
                try:
                    wrapped.encode('cp1252')
                except UnicodeEncodeError as exc:
                    raise ValueError('PDF export currently supports Western European text. Use the reviewed text export for other scripts.') from exc
                c.drawString(42,y,wrapped);y-=14
        c.showPage()
    c.save()
    raw=out.getvalue()
    with store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        store.event(db,'redacted_copy_exported',redaction_id,{'derivative_sha256':hashlib.sha256(raw).hexdigest()})
    return raw
