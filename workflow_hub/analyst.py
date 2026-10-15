"""Transparent analyst workflow guidance. No invented rules or compliance score."""
PLAYBOOKS = {
 'supplier-onboarding':[
  'Confirm the service, business owner, criticality and data involved.',
  'Map the evidence to your organisation\'s approved supplier-control requirements.',
  'Check legal entity, document dates, scope, issuer and independently verifiable sources.',
  'Request evidence for missing or contradictory controls; record an owner and due date.',
  'Assess residual risk against the organisation\'s risk appetite and escalate to the authorised owner.',
  'Record the human decision, conditions and next review date.'
 ],
 'policy-review':[
  'Confirm the policy owner, version, approval date, scope and applicable internal requirements.',
  'Compare each material claim with implementation evidence.',
  'Record unclear wording, missing responsibilities and unsupported assertions with page references.',
  'Propose amendments for the policy owner and track their decision.'
 ],
 'incident-triage':[
  'Record observed facts, discovery time and affected service. Separate facts from assumptions.',
  'Follow the organisation\'s incident procedure and notify its designated response team.',
  'Preserve authorised evidence and avoid further unnecessary copies of personal data.',
  'Let the incident owner and privacy/security specialists assess severity and reporting duties.',
  'Track containment, decisions, recovery evidence and lessons learned.'
 ],
 'control-testing':[
  'Define the control objective, owner, expected behaviour and test scope.',
  'Obtain permission and choose a safe test environment with minimal access.',
  'Record inputs, expected results, actual results, time and source evidence.',
  'Distinguish an expected denial from a control failure.',
  'Document exceptions, remediation owners and retest evidence for human review.'
 ]}


def guidance(store, case_id, task):
    if task not in PLAYBOOKS:
        raise ValueError('Unknown analyst workflow')
    snap=store.snapshot()
    docs=[d for d in snap['documents'] if d['case_id']==case_id]
    findings=[f for f in snap['findings'] if f['case_id']==case_id]
    gaps=[f for f in findings if f['status'] in ('GAP','CONFLICT','CLAIM_ONLY')]
    return {'case_id':case_id,'task':task,'source_documents':len(docs),
            'next_steps':PLAYBOOKS[task],
            'evidence_actions':[{'control':f['control'],'source':f['source'],'page':f['page'],'status':f['status'],
                                 'next_action':'Resolve with the control owner: '+f['note']} for f in gaps],
            'decision':'HUMAN_REVIEW_REQUIRED',
            'boundary':'Procedural guidance, not a legal conclusion or a substitute for employer policy. Absence of findings does not mean controls passed.'}
