# Palm92 Content Studio

Local-first content desk for turning Faith's raw ideas into reviewed Palm92 posts. The first release is a static browser app with no account, server, API key, AI credit or paid dependency.

## Run it

Open `index.html` in a current browser. Draft cards are stored in that browser's local storage. Use **Export my content** to download a JSON backup before changing devices or clearing browser data.

## Workflow

1. Capture a rough idea or voice-note transcript.
2. Build a writing prompt and paste it into ChatGPT, Codex/Astra or a locally installed open model.
3. Paste the generated draft into the card and edit it.
4. Mark it approved only after checking facts, voice, privacy, and visual direction.
5. Copy approved copy into Metricool or the platform's native composer. Posting is deliberately not automatic.

## Boundaries

- This app does not send data to a server or call an AI API.
- This app does not publish, schedule, scrape trends, or guarantee engagement.
- Browser storage is device and browser specific. Export backups regularly.
- OpenArt and HeyGen are optional creation tools. Use them only when the chosen output fits available free access. Use the video brief in `docs/FREE_TOOLCHAIN.md` to make a no-credit version with your phone and free editing tools.

## Project files

- `docs/FREE_TOOLCHAIN.md`: tool scout, limits and fallback route.
- `docs/VOICE_AND_GOVERNANCE.md`: voice, editorial and review rules.
- `content/week-one.md`: the first seven-day Palm92 content plan.
