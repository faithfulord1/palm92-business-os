"""Explicit CLI-only live delivery. Never called by AI or the dashboard."""
import json
import os
import re
import urllib.request
import uuid
from datetime import datetime, timezone
from adapters import NoRedirect, channel_payload, verify_whatsapp_signature
from core import now


def receive_whatsapp(store, raw, signature):
    secret = os.environ.get('PALM92_META_APP_SECRET','')
    if not verify_whatsapp_signature(raw,signature,secret):
        raise ValueError('Invalid webhook signature')
    data = json.loads(raw)
    phone_id = os.environ.get('PALM92_WHATSAPP_PHONE_ID','')
    if not phone_id:
        raise ValueError('Configure the intended business phone ID')
    received = 0
    with store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        db.execute('CREATE TABLE IF NOT EXISTS inbox(id TEXT PRIMARY KEY,sender TEXT,at REAL,body TEXT)')
        for entry in data.get('entry',[]):
            for change in entry.get('changes',[]):
                value = change.get('value',{})
                if value.get('metadata',{}).get('phone_number_id') != phone_id:
                    continue
                for message in value.get('messages',[]):
                    if message.get('type') != 'text':
                        continue
                    stamp = float(message['timestamp'])
                    if stamp > datetime.now(timezone.utc).timestamp()+60:
                        raise ValueError('Webhook timestamp is in the future')
                    sender = message['from']
                    if not re.fullmatch(r'[1-9][0-9]{6,14}',sender):
                        raise ValueError('Invalid sender')
                    cur = db.execute('INSERT OR IGNORE INTO inbox VALUES(?,?,?,?)',
                                     (message['id'],sender,stamp,message['text']['body']))
                    received += cur.rowcount
        store.event(db,'whatsapp_webhook_imported','inbox',{'new_messages':received})
    return {'new_messages':received}


def transport(url, body, headers):
    request = urllib.request.Request(url,data=json.dumps(body).encode(),headers={'Content-Type':'application/json',**headers})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    with opener.open(request,timeout=30) as response:
        raw = response.read(1_000_001)
        if len(raw)>1_000_000:
            raise ValueError('Unexpected provider response size')
        return {'status':response.status,'headers':dict(response.headers),'body':json.loads(raw) if raw else {}}


def send(store, action_id, confirm_hash, consent=False, http=transport):
    if os.environ.get('PALM92_ALLOW_CLOUD_CONNECTORS') != 'YES':
        raise ValueError('Private workspace is offline. Cloud connectors require separate enablement.')
    if os.environ.get('PALM92_ENABLE_LIVE_SEND') != 'YES':
        raise ValueError('Live delivery is disabled. PALM92_ENABLE_LIVE_SEND=YES is required.')
    item = store.action(action_id)
    if item['state'] != 'APPROVED_FOR_EXPORT' or item['content_hash'] != confirm_hash:
        raise ValueError('An approved, unchanged draft and matching confirmation hash are required')
    payload = channel_payload(item)
    headers = {}
    if item['channel'] == 'linkedin':
        token = os.environ.get('PALM92_LINKEDIN_TOKEN','')
        version = os.environ.get('PALM92_LINKEDIN_VERSION','')
        if not token or not re.fullmatch(r'\d{6}',version):
            raise ValueError('LinkedIn token and supported API version are required')
        if not re.fullmatch(r'urn:li:(person|organization):[A-Za-z0-9_-]+',item['destination']):
            raise ValueError('Expected LinkedIn person or organisation URN')
        if len(item['text']) > 3000:
            raise ValueError('LinkedIn draft exceeds 3000 characters')
        url = 'https://api.linkedin.com/rest/posts'
        headers = {'Authorization':'Bearer '+token,'LinkedIn-Version':version,'X-Restli-Protocol-Version':'2.0.0'}
    elif item['channel'] == 'whatsapp':
        if consent is not True:
            raise ValueError('Confirm recipient consent before sending')
        token = os.environ.get('PALM92_WHATSAPP_TOKEN','')
        phone = os.environ.get('PALM92_WHATSAPP_PHONE_ID','')
        version = os.environ.get('PALM92_META_VERSION','')
        if not token or not phone.isdigit() or not re.fullmatch(r'v\d+\.\d+',version):
            raise ValueError('WhatsApp business token, phone ID and API version are required')
        if len(item['text']) > 4096:
            raise ValueError('WhatsApp text exceeds 4096 characters')
        with store.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS inbox(id TEXT PRIMARY KEY,sender TEXT,at REAL,body TEXT)')
            row = db.execute('SELECT MAX(at) AS latest FROM inbox WHERE sender=?',(payload['to'],)).fetchone()
        if not row['latest'] or not 0 <= datetime.now(timezone.utc).timestamp()-row['latest'] < 86400:
            raise ValueError('No verified inbound message in the last 24 hours. Approved templates are not implemented.')
        payload.pop('_handoff',None)
        url = f'https://graph.facebook.com/{version}/{phone}/messages'
        headers = {'Authorization':'Bearer '+token}
    else:
        raise ValueError('This channel supports export only')
    # Commit the claim before the network request. Concurrent/repeated sends are blocked.
    with store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        current = json.loads(db.execute('SELECT data FROM actions WHERE id=?',(action_id,)).fetchone()['data'])
        if current['state'] != 'APPROVED_FOR_EXPORT' or current['content_hash'] != confirm_hash:
            raise ValueError('Action already claimed or changed')
        current.update(state='SENDING',attempt_id=uuid.uuid4().hex)
        db.execute('UPDATE actions SET data=? WHERE id=?',(json.dumps(current),action_id))
        store.event(db,'delivery_started',action_id,{'hash':confirm_hash,'attempt':current['attempt_id']})
    try:
        response = http(url,payload,headers)
        if not 200 <= response['status'] < 300:
            raise ValueError('Provider did not confirm success')
        if item['channel'] == 'linkedin':
            receipt = next((v for k,v in response['headers'].items() if k.lower() == 'x-restli-id'),None)
        else:
            receipt = response['body'].get('messages',[{}])[0].get('id')
        if not receipt:
            raise ValueError('No delivery receipt')
        current.update(state='SENT',receipt=receipt,sent_at=now())
    except Exception:
        current.update(state='DELIVERY_UNCERTAIN')
        # Never auto-retry: a provider may have accepted the request before a timeout.
    with store.connect() as db:
        db.execute('BEGIN IMMEDIATE')
        db.execute('UPDATE actions SET data=? WHERE id=?',(json.dumps(current),action_id))
        store.event(db,'delivery_outcome',action_id,{'state':current['state'],'receipt':current.get('receipt')})
    return current


def main():
    import argparse
    from core import Store
    parser = argparse.ArgumentParser(description='Explicitly send one reviewed action or import a signed WhatsApp webhook')
    parser.add_argument('--data',required=True)
    sub = parser.add_subparsers(dest='command',required=True)
    publish = sub.add_parser('send'); publish.add_argument('id'); publish.add_argument('--confirm-hash',required=True); publish.add_argument('--consent',action='store_true')
    inbox = sub.add_parser('receive'); inbox.add_argument('file'); inbox.add_argument('--signature',required=True)
    args = parser.parse_args(); store = Store(args.data)
    if args.command == 'send':
        result = send(store,args.id,args.confirm_hash,args.consent)
    else:
        from pathlib import Path
        result = receive_whatsapp(store,Path(args.file).read_bytes(),args.signature)
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
