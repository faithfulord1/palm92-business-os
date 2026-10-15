#!/usr/bin/env python3
"""Palm92 Workflow Hub command line."""
import argparse
import json
import os
from pathlib import Path
from core import Store


def main():
    parser = argparse.ArgumentParser(description='Palm92 local workflow hub')
    parser.add_argument('--data',default=os.environ.get('PALM92_DATA_DIR',str(Path.home()/'.palm92-workflow-hub')))
    sub = parser.add_subparsers(dest='command',required=True)
    serve = sub.add_parser('serve'); serve.add_argument('--port',type=int,default=8792)
    sub.add_parser('doctor')
    demo = sub.add_parser('demo'); demo.add_argument('--case',default='DEMO-ONLY')
    ingest = sub.add_parser('ingest'); ingest.add_argument('file'); ingest.add_argument('--case',required=True); ingest.add_argument('--engine',choices=['basic','docling'],default='basic')
    export = sub.add_parser('export'); export.add_argument('--case',required=True); export.add_argument('--output',required=True)
    speech = sub.add_parser('transcribe'); speech.add_argument('file'); speech.add_argument('--consent',action='store_true'); speech.add_argument('--output',required=True)
    sub.add_parser('audit')
    args = parser.parse_args()
    if args.command == 'serve':
        from server import serve
        return serve(args.data,args.port)
    store = Store(args.data)
    if args.command == 'doctor':
        from adapters import capabilities
        result = capabilities()
    elif args.command == 'ingest':
        source = Path(args.file)
        result = store.ingest(source.name,source.read_bytes(),args.case,args.engine)
    elif args.command == 'demo':
        source = Path(__file__).with_name('examples')/'fictional-supplier.md'
        doc = store.ingest(source.name,source.read_bytes(),args.case)
        result = {'document':doc,'triage':store.assess({'vendor':'Fictional Harbour Training Ltd','mfa':True,'encryption':None,'recovery_test':False,'independent_assurance':None,'certificate_expiry':'2025-12-31'})}
    elif args.command == 'audit':
        result = store.audit()
    elif args.command == 'transcribe':
        from adapters import transcribe
        result = transcribe(args.file,args.consent)
        target = Path(args.output); target.mkdir(parents=True,exist_ok=True)
        (target/'transcript.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        (target/'transcript.srt').write_text(result['srt'],encoding='utf-8')
        result = {'status':'UNREVIEWED_TRANSCRIPT','output':str(target)}
    elif args.command == 'export':
        result = store.evidence_export(args.case)
        target = Path(args.output); target.mkdir(parents=True,exist_ok=True)
        for name,key in [('register.csv','register_csv'),('knowledge.md','knowledge_markdown')]:
            (target/name).write_text(result[key],encoding='utf-8')
        (target/'evidence.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        result = {'output':str(target),'findings':len(result['findings'])}
    print(json.dumps(result,indent=2,ensure_ascii=False))


if __name__ == '__main__':
    main()
