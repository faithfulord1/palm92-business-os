# Palm92 project recovery audit

Checked 17 October 2026 through the connected GitHub account. This is a source-tree, README and latest-workflow audit, not proof of production readiness. No projects are marked complete merely because their latest workflow passed. Latest runs can be older than the current commit; exact-head CI remains a separate check.

| Repository | Files in inspected tree | Latest workflow | Next verification |
| --- | ---: | --- | --- |
| [palm92-repoguard](https://github.com/faithfulord1/palm92-repoguard) | 64 | [success](https://github.com/faithfulord1/palm92-repoguard/actions/runs/36271069853) | Preserve measured benchmark evidence. Verify current experiment separately from CPU CI; do not invent improved fix rates. |
| [palm92-verified-request](https://github.com/faithfulord1/palm92-verified-request) | 7 | [success](https://github.com/faithfulord1/palm92-verified-request/actions/runs/38363798013) | Tree has only seven files; reconcile MVP/connector expectations with actual implementation and verify authority-gate behavior. |
| [palm92-judgmentos](https://github.com/faithfulord1/palm92-judgmentos) | 18 | [success](https://github.com/faithfulord1/palm92-judgmentos/actions/runs/38450283948) | Inspect core workflow, run required checks against current head, verify deployment and integrations. |
| [palm92-situation-intelligence](https://github.com/faithfulord1/palm92-situation-intelligence) | 26 | [success](https://github.com/faithfulord1/palm92-situation-intelligence/actions/runs/34714610017) | Inspect core workflow, run required checks against current head, verify deployment and integrations. |
| [palm92-capital-intelligence](https://github.com/faithfulord1/palm92-capital-intelligence) | 20 | [success](https://github.com/faithfulord1/palm92-capital-intelligence/actions/runs/36427972858) | Inspect core workflow, run required checks against current head, verify deployment and integrations. |
| [palm92-lead-recovery-os](https://github.com/faithfulord1/palm92-lead-recovery-os) | 18 | [success](https://github.com/faithfulord1/palm92-lead-recovery-os/actions/runs/33961212296) | Inspect core workflow, run required checks against current head, verify deployment and integrations. |
| [Palm92-ai-test-copilot](https://github.com/faithfulord1/Palm92-ai-test-copilot) | 34 | [success](https://github.com/faithfulord1/Palm92-ai-test-copilot/actions/runs/34067087656) | Inspect core workflow, run required checks against current head, verify deployment and integrations. |
| [safevoice-intelligence](https://github.com/faithfulord1/safevoice-intelligence) | 18 | [success](https://github.com/faithfulord1/safevoice-intelligence/actions/runs/36423607888) | Inspect core workflow, run required checks against current head, verify deployment and integrations. |
| [property-pilot-ai](https://github.com/faithfulord1/property-pilot-ai) | 2 | No run returned | Historical pointer/archive. Work in its canonical repository; do not build a competing application. |
| [jobshield-ai](https://github.com/faithfulord1/jobshield-ai) | 5 | No run returned | Static demo has no returned CI run. Add and run a validation workflow before any completion claim. |
| [palm92-motionguard-ai](https://github.com/faithfulord1/palm92-motionguard-ai) | 14 | [success](https://github.com/faithfulord1/palm92-motionguard-ai/actions/runs/36423674198) | Inspect core workflow, run required checks against current head, verify deployment and integrations. |
| [Vendor-Due--Diligence-Agent](https://github.com/faithfulord1/Vendor-Due--Diligence-Agent) | 16 | [success](https://github.com/faithfulord1/Vendor-Due--Diligence-Agent/actions/runs/33964883615) | Inspect core workflow, run required checks against current head, verify deployment and integrations. |
| [winners-connect-lewisham](https://github.com/faithfulord1/winners-connect-lewisham) | 79 | [success](https://github.com/faithfulord1/winners-connect-lewisham/actions/runs/33944352343) | Inspect core workflow, run required checks against current head, verify deployment and integrations. |
| [propertypilot-ai2](https://github.com/faithfulord1/propertypilot-ai2) | 2 | No run returned | Historical pointer/archive. Work in its canonical repository; do not build a competing application. |
| [PropertyPilot-AI-](https://github.com/faithfulord1/PropertyPilot-AI-) | 44 | [success](https://github.com/faithfulord1/PropertyPilot-AI-/actions/runs/38040903239) | Inspect core workflow, run required checks against current head, verify deployment and integrations. |
| [palm92-lead-recovery](https://github.com/faithfulord1/palm92-lead-recovery) | 1 | No run returned | Historical pointer/archive. Work in its canonical repository; do not build a competing application. |
| [palm92-business-os](https://github.com/faithfulord1/palm92-business-os) | 19 | [success](https://github.com/faithfulord1/palm92-business-os/actions/runs/38686116062) | Jarvis recovery in tools/jarvis; finish real adapter, persistence and delivery-receipt acceptance tests from Chief of Staff architecture. |
| [palm92-governed-agent-mcp](https://github.com/faithfulord1/palm92-governed-agent-mcp) | 24 | [success](https://github.com/faithfulord1/palm92-governed-agent-mcp/actions/runs/37449989142) | Inspect core workflow, run required checks against current head, verify deployment and integrations. |
| [palm92-grc-evidence-vault](https://github.com/faithfulord1/palm92-grc-evidence-vault) | 10 | [success](https://github.com/faithfulord1/palm92-grc-evidence-vault/actions/runs/39035583549) | Inspect core workflow, run required checks against current head, verify deployment and integrations. |

## Jarvis Plan B completed work

Recovered the existing local package; corrected its invalid Python prompt; compiled/imported it and passed six offline server regression checks. Started it using Blender 5.2's bundled Python: its log reports listening at 127.0.0.1:4700. This execution session cannot access localhost sockets, so a browser page load and actual Ollama-generated response remain unverified. The standard WindowsApps Python alias was unusable. The launcher now searches real installed runtimes and skips that alias. No security settings were disabled.

## Reusable free foundations checked

- Existing Python standard-library HTTP server plus [Ollama](https://github.com/ollama/ollama): retain the working local architecture, no paid API required.
- [LangGraph](https://github.com/langchain-ai/langgraph): checkpointing and human-interrupt patterns if the current task engine needs durable agent execution.
- [Activepieces](https://github.com/activepieces/activepieces): evaluate its self-hosted automation components against the existing n8n workflow rather than introducing both blindly.
- [Prefect](https://github.com/PrefectHQ/prefect): self-hosted workflow retries, scheduling and monitoring patterns for Python work.
- [n8n](https://github.com/n8n-io/n8n): an existing Palm92 workflow already uses it; review its fair-code licence and available self-hosted features before reuse.

These are candidates, not installed integrations or proven fits for every project. Free software can still require an always-on laptop or hosting resources. No third-party source was copied into this repair.

## Remaining execution boundaries

LinkedIn and email desks currently draft only. A working authorised adapter, duplicate-send prevention, failure recovery and delivery receipt must be demonstrated before enabling unattended sending. A general LinkedIn posting permission is not proof of personal inbox access.

GitLab profile recovered from earlier account context: https://gitlab.com/faithfulord1 . Current projects could not be read in this session, and no GitLab connector is exposed. Do not infer zero projects from the earlier screenshot. Preserve the prior decision to combine RepoGuard/Governed Agent work rather than create another competing GitLab project.

Priority order: restore and verify Jarvis chat, persist tasks across restart, complete one real communication adapter with delivery evidence, then verify the remaining canonical applications against concrete acceptance tests. Keep portfolio demos distinct from production services. New repository links supplied by Faithful should be added to this same audit.
