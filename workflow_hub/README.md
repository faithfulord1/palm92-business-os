# Palm92 Private Analyst

A local Windows-oriented workspace for evidence handling, assisted redaction, GRC/TPRM review and separately approved communications. Built inside the existing Palm92 Business OS repository.

**AI investigates. Humans decide.**

## Current maturity

Working local reference application with automated tests. Not a certified compliance product, not an independent security assessment, and not approved for any employer's real personal data. Test with fictional documents first. Employer/charity approval and a device security review are still needed before processing their information.

The application does not guarantee prevention of data breaches, complete anonymisation, regulatory compliance, or expert-level judgement. It makes source checks, missing evidence and human decisions visible.

## Start on a Windows laptop

### Packaged app

The GitHub Actions workflow `Private Workflow Hub` builds a Windows folder named `Palm92PrivateAnalyst-Windows`. Download the artifact from a **successful** run, extract the complete folder, and open `Palm92PrivateAnalyst.exe`. The folder must stay together. This is an unsigned prototype build; do not bypass an employer's software restrictions.

The packaged app includes PDF text extraction, encryption, reviewed text redaction and the dashboard. Docling OCR/model weights, whisper.cpp and image/video models are separate optional installations, not included in the executable. A package must be tested on the target Windows machine before claiming Windows compatibility is verified.

### Source launcher (Plan B)

Install Python 3.12 from the official Python website. In this repository, double-click `workflow_hub/start-windows.cmd`. It creates an isolated environment, installs the core dependencies, and opens a small passphrase dialog. This setup step uses the internet to install packages; ordinary private operation defaults to external connectors disabled.

1. Choose a separate workspace label for each employer, charity and your public Palm92 content.
2. Set a strong passphrase of at least 12 characters. There is no recovery if lost.
3. Your browser opens the private dashboard on `127.0.0.1:8792`.
4. Import a **fictional** sample first, then test the privacy and evidence workflows.
5. Use **Lock workspace** when finished. The process also closes after 15 minutes without API activity. The browser clears its displayed content after its own idle timer.

The desktop launcher forces external connectors and live sends OFF, even if those environment variables were inherited. The CLI can be used for a separate explicitly configured public-content workspace.

## What works

- Encrypted originals and encrypted database on disk using AES-256-GCM and a password-derived scrypt key. SQLite operates in memory, with authenticated encrypted snapshots saved atomically.
- Separate workspace folders, passwords and case references.
- Text, Markdown, CSV and basic text-PDF imports with source SHA-256 and page references. Blank/image-only PDFs fail closed when basic extraction finds no text.
- Optional Docling adapter with remote services/plugins disabled. Model download is a distinct setup operation; runtime sets offline model-cache flags.
- Case-scoped exact text search, source quotation verification and human-recorded evidence findings.
- Tri-state questionnaire triage: true is CLAIM_ONLY, false is GAP, absent is UNKNOWN. No invented compliance score or supplier approval.
- Procedural next steps for supplier onboarding, policy review, control testing and incident triage.
- Local redaction candidate detection and manual term removal. Each preview has a hash; approval binds the reviewer to that preview.
- Fresh text-only PDF derivatives from reviewed text. No original PDF objects, images, attachments, JavaScript or metadata are copied. This sacrifices original formatting, graphics and signatures.
- Draft/approval/export queue for LinkedIn, WhatsApp, GitHub, media and Asana task handoffs.
- Local AI drafting through Ollama or a configured local OpenAI-compatible server, without action tools.
- whisper.cpp command adapter for authorised WAV recordings; CLI only.
- ComfyUI graph export, not a bundled image/video model.
- Read-only GitHub checks when an operator explicitly enables external connectors.
- Explicit CLI-only LinkedIn and WhatsApp delivery adapters, disabled by default, with receipt tracking and duplicate-send protection. These have mocked contract tests, not live account tests.

## Everyday private workflow

### 1. Intake

Open the appropriate organisation's workspace. Confirm you are authorised to use that device and application. Select a case reference and import the document. The original remains encrypted; extracted pages are stored inside the encrypted database.

### 2. Privacy review

Open Privacy & redaction. Run the candidate scan. Add names, addresses, identifiers or sensitive phrases that the detector missed. Review every page against the original and consider contextual re-identification. State the purpose and rationale, then approve the exact preview.

Download only when needed. **Any exported PDF, CSV, Markdown, JSON or transcript is unencrypted outside the vault.** Save it only in an approved location and inspect it before disclosure. Do not assume that a redacted document is anonymous.

### 3. Evidence review

Search the case; select a supporting passage. Record control ID, evidence status, rationale and reviewer. VERIFIED is a human judgement that must be justified. A matching quote demonstrates extraction provenance, not document authenticity or control effectiveness.

### 4. Next action

Open Supplier review and choose the appropriate workflow. Work through the checklist and case-specific gaps. Apply your organisation's approved policies, risk appetite and escalation route. Use local AI to draft explanations or questions, then verify them yourself.

### 5. Separate communications

Use a separate public-content workspace for LinkedIn. Put only approved public facts into the draft. Prepare supplier follow-ups for the exact authorised recipient. Approval is for the exact content and destination. Export alone does not send. Asana handoff is a JSON task payload; it is not a live Asana integration.

## Optional tool setup

| Source tool | Implementation here | External requirement |
|---|---|---|
| Docling | Local parsing adapter, original provenance | Install `requirements-docling.txt`, prefetch official models, test OCR on target device |
| whisper.cpp | WAV transcription adapter | Official binary plus local model; set two variables below |
| llama.cpp | Local compatible API adapter | Local llama-server and downloaded model |
| Jan | Same compatible API adapter | Enable a local-only server; confirm it does not forward to cloud |
| AnythingLLM | Case Markdown export | Import only into an approved local workspace; review telemetry/provider settings |
| Open WebUI | Case Markdown export and local-engine interoperability | Optional separate installation; do not expose it publicly |
| OpenHands | Engineering handoff through GitHub draft tasks | Optional code-only sandbox; never mount private vaults into coding agents |
| InvokeAI | Public media briefs | Optional separate local creative tool; no direct connector claimed |
| AUTOMATIC1111 | Public media briefs | Optional alternative to ComfyUI; no direct connector claimed |
| ComfyUI | API-format graph export and status adapter | Compatible checkpoint and local GPU/CPU capacity; no render verified |

Ollama is the first local model route. Jan/llama.cpp are alternatives, not mandatory additional installations. Avoid installing duplicate model runtimes without a concrete need.

For Docling in the source environment:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-docling.txt
# Run the installed Docling model downloader during approved online setup.
.venv\Scripts\docling-tools.exe models download
```

Then test conversion with model caches available and network disconnected. Failure to locate model weights is a blocker, not permission to upload documents to a cloud service. This optional integration has not been run with real model weights in the build environment.

For local models, configure the source launch environment:

```powershell
$env:PALM92_MODEL = 'the-exact-name-of-your-downloaded-model'
$env:PALM92_OLLAMA_URL = 'http://127.0.0.1:11434'
```

For Jan/llama.cpp/LM Studio, set `PALM92_LOCAL_API_URL` to a loopback `/v1` endpoint and `PALM92_LOCAL_MODEL_ATTESTED=YES` only after confirming its model and provider settings. An endpoint on localhost can still forward data elsewhere: the endpoint address alone cannot prove privacy.

For transcription:

```powershell
$env:PALM92_WHISPER_BIN = 'C:\approved-tools\whisper-cli.exe'
$env:PALM92_WHISPER_MODEL = 'C:\approved-models\ggml-base.bin'
.venv\Scripts\python.exe hub.py transcribe approved-recording.wav --consent --output C:\approved-local-folder\transcript
```

Transcripts are unreviewed and exported unencrypted. Check names, numbers, speaker attribution and omissions. Audio and model binaries are not bundled.

## External delivery, only from an approved workspace

Delivery code is present to make the integration reviewable. It has not been authenticated with live LinkedIn or WhatsApp credentials. No messages were sent during development.

The CLI requires both `PALM92_ALLOW_CLOUD_CONNECTORS=YES` and `PALM92_ENABLE_LIVE_SEND=YES`, a previously approved draft, and the exact content hash supplied again at execution. Set tokens through a secret manager or the operator environment, never in GitHub or the dashboard.

- LinkedIn: `PALM92_LINKEDIN_TOKEN`, `PALM92_LINKEDIN_VERSION` (a currently supported YYYYMM). The account must have the necessary publishing permissions; destination is a person/organisation URN.
- WhatsApp: `PALM92_WHATSAPP_TOKEN`, `PALM92_WHATSAPP_PHONE_ID`, `PALM92_META_VERSION`, `PALM92_META_APP_SECRET`. Only replies within 24 hours of a signed imported inbound event are supported. Recipient consent must be confirmed. Approved-template delivery is not implemented.
- WhatsApp inbound events can be imported with `delivery.py receive file.json --signature ...` after a separate secure receiver captures the raw signed webhook. **No publicly hosted webhook receiver is provided.**
- A timeout leaves DELIVERY_UNCERTAIN; no automatic retry or reset button is provided. Check the provider before taking any further action.
- GitHub status uses public reads or `PALM92_GITHUB_TOKEN`; no repository mutations from the app.
- Asana payloads are reviewed exports. Credentials, project authorisation and live delivery remain unconnected.

## API integration for other Palm92 apps

The local HTTP API uses a fresh per-process bearer token printed by the CLI or passed in the private launch URL fragment. It requires a loopback Host, refuses other browser Origins, and sends no CORS permissions. It must not be deployed publicly or used as a multi-user service.

Routes: `GET /api/state`, `/api/document?id=...`, `/api/audit`, `/api/export?case=...`; `POST /api/ingest`, `/api/search`, `/api/finding`, `/api/assess`, `/api/analyst`, `/api/privacy-preview`, `/api/privacy-approve`, `/api/privacy-export`, `/api/draft`, `/api/approve`, `/api/export-action`, `/api/ai`, `/api/github`, `/api/media`, `/api/lock`.

Existing Vendor Due Diligence Agent and GRC Evidence Vault schemas differ from this app. JSON export is a handoff format; automatic synchronisation into those apps is not claimed. A trusted local adapter must map fields and preserve provenance before production integration.

## Verification

```bash
python -m unittest discover -s workflow_hub/tests -v
```

Tests cover encrypted persistence, wrong password/tampering, source matching, case isolation, redaction review and clean PDF output, unknown risk inputs, unapproved exports, signed webhook validation/deduplication, service-window checks, duplicate delivery, uncertain delivery, offline mode and HTTP authentication/origin checks. Adapter tests use fixtures/mocks, not paid services.

## Privacy and deployment boundaries

- Use a separate operating-system login and employer-approved disk encryption. The app cannot protect an unlocked screen, malware, browser extensions, OS swap, crash dumps or someone controlling the device.
- Encryption keys and decrypted data exist in RAM while unlocked. Python does not guarantee secure memory wiping. Locking stops the local service; OS process isolation and device security remain necessary.
- Back up the **complete encrypted workspace**, including its salt and encrypted originals, to an approved encrypted destination. Losing salt or passphrase can make recovery impossible.
- The event chain detects modification relative to a trusted checkpoint; a local administrator can rewrite the whole chain. It is not WORM storage or a digital signature service.
- The detector is heuristic and incomplete. It does not certify anonymity, analyse original image context, or reliably detect every person, diagnosis or indirect identifier.
- Basic PDF extraction is not OCR and can misorder tables. Docling requires separate installation and validation. DOCX is accepted only through the optional parser and rejected if reliable page provenance is unavailable; export to PDF first.
- No background scheduler, public deployment, automatic approvals, production identity management, cross-device sync or clinical/legal decision authority is included.
- Retention/deletion policy and managed-device rollout must be agreed with the organisation before real records are onboarded. This prototype does not enforce a retention schedule.

## Sources checked during implementation

- [Docling advanced/offline options](https://docling-project.github.io/docling/usage/advanced_options/)
- [Ollama chat API](https://docs.ollama.com/api/chat)
- [whisper.cpp](https://github.com/ggml-org/whisper.cpp)
- [AnythingLLM desktop privacy](https://docs.anythingllm.com/installation-desktop/privacy)
- [ComfyUI server routes](https://docs.comfy.org/development/comfyui-server/comms_routes)
- [LinkedIn Posts API](https://learn.microsoft.com/en-us/linkedin/marketing/community-management/shares/posts-api)
- [ICO: secure document disclosure](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/security/disclosing-documents-to-the-public-securely/)
- [ICO: pseudonymisation](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/data-sharing/anonymisation/pseudonymisation/)

The supplied video/PDF was a tool-discovery source, not evidence that every marketing claim was accurate. For example, AnythingLLM's own policy describes optional telemetry; the transcript's blanket zero-telemetry claim is not adopted.
