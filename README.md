# Palm92 Business OS

An Astro and Vercel-ready foundation for Palm92 Intelligence, combining a conversion website, documentation-grounded support, human escalation and GitHub-based recovery.

## Local setup

```bash
npm install
cp .env.example .env.local
npm run dev
```

The support page runs in safe preview mode until `PUBLIC_SUPPORT_WEBHOOK_URL` is configured.

## Deployment

1. Create or connect the GitHub repository.
2. Import it into Vercel. Vercel detects Astro automatically.
3. Add `PUBLIC_SUPPORT_WEBHOOK_URL` only after the n8n webhook is secured and tested.
4. Use preview deployments for review before promoting to production.

## n8n workflow

Import `workflows/palm92-support-agent.n8n.json`, then configure these credentials as environment variables without committing their values:

- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `PALM92_RETRIEVAL_URL`
- `PALM92_RETRIEVAL_TOKEN`

The template is inactive by default. Add an authenticated case store and a human-notification destination before activation. Test retrieval, refusal, repeated-failure escalation, sensitive-topic escalation and webhook abuse protection.

## Governance

The agent may answer only from approved documentation. It must escalate uncertainty, failed guidance, frustration, suspected bugs and sensitive matters. See `knowledge-base/support-policy.md` and `docs/INCIDENT-RESPONSE.md`.
