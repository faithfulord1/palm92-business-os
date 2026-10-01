# Chief of Staff Resilience Architecture

## Principle
Palm92 Advantage is one governed Chief of Staff with multiple communication and execution adapters.

## Layers
- Source/version evidence: GitHub
- Governance engine: Palm92 Governed Agent MCP
- Public Python runtime: Render
- Fast/fallback edge path: Cloudflare Workers when provisioned and verified
- Messaging adapters: Telegram first, WhatsApp second
- Work adapters: Gmail and Google Calendar
- Human approval: Faithful
- Audit: correlation ID per request/action, decision record, channel result

## Failure behaviour
A channel failure must not corrupt the core task. Queue/retry only safe idempotent operations. Consequential sends require approval and deduplication. If a provider is unavailable, preserve the pending action and surface the blocker rather than inventing success.

## Acceptance tests
1. Telegram inbound reaches the Chief of Staff and receives a governed response.
2. A consequential Telegram request is held for approval rather than executed silently.
3. Gmail can be inspected/drafted without sending until approved.
4. Calendar reads are non-destructive; writes require the applicable approval rule.
5. WhatsApp adapter uses the same governance and audit model when credentials are connected.
6. Hosting health failure is detectable and a fallback path is documented/tested.
