# Free and open toolchain scout

Checked 7 November 2026. Availability can change. No workflow here assumes a paid AI generation or an unlimited credit balance.

| Need | Primary route | Free route and limits | Reliable fallback |
|---|---|---|---|
| Planning and copy | ChatGPT, Codex, and the available Astra reasoning model in this workspace | Use the existing ChatGPT access for briefs and review. Keep this static app independent of API calls. | Copy the generated prompt into any compatible local model or work from the template manually. |
| Private/open model | Ollama on Linux with Qwen3 4B, Apache 2.0 | The app can call Ollama's local `/api/chat` endpoint without an API key. Qwen3 4B is about 2.5 GB. CPU speed depends on the computer; larger models need more memory. | Use the writing prompt in ChatGPT/Codex. No content work is blocked by local hardware. |
| Repository and recovery | GitHub, branch `feat/palm92-content-studio` in `faithfulord1/palm92-business-os` | The source files are versioned in GitHub. Standard Actions runners are free on public repositories; this MVP does not require Actions. | Export the browser cards as JSON and keep a local copy. |
| Coding and maintenance | Codex | Use the existing Codex workspace and GitHub integration. No separate paid coding API is required for this static MVP. | Edit the static HTML/CSS/JS directly in Codex or any text editor. |
| Stills | OpenArt, only when an affordable image mode is listed | The connected OpenArt account is Free with 25 credits. The live model list shows some still image modes at 15-20 credits, but no video mode within the balance. Avoid spending credits on routine drafts. | Use a phone photo, public-domain/appropriately licensed source media, or a designed text card. Keep citations and licences with the asset. |
| Video | Phone-recorded footage, edited on Linux with FFmpeg; Blender can add titles and simple motion after installation | FFmpeg is present in the current Linux workspace; Blender and Ollama are not. The current workspace reports 9.7 GiB RAM and no detected NVIDIA utility. This is only the build container, not a measurement of Faith's laptop. | Export a no-cost vertical edit using phone footage, captions, licensed music, and FFmpeg. Do not promise generated cinematic footage without a usable generator. |
| Avatar / AI video | HeyGen is optional | The connected HeyGen account reports Free. Official pricing currently lists 3 watermarked videos/month, up to 1 minute each. That is useful for a short test, not a guaranteed premium campaign master. | Use Faith's real recorded voice and footage, with restrained editing and captions. |
| Scheduling / metrics | Metricool if the target social account is connected | The connected brand currently exposes Instagram data for `faithfulord`; LinkedIn publishing access was not verified. Scheduling requires checking the target network connection and post type in Metricool. | Prepare approved copy and schedule natively in LinkedIn/Instagram. Keep approval before publication. |

## Install local drafting on Linux

Install Ollama from its official Linux instructions, then run:

```sh
ollama pull qwen3:4b
ollama serve
```

In a second terminal, run `./run-local.sh` from this folder and open `http://127.0.0.1:8000`. Click **Build my writing prompt**, then **Draft with my local model**. The app posts only to `http://127.0.0.1:11434/api/chat`. Keep Ollama bound to this computer. Do not set `OLLAMA_ORIGINS=*` or expose its port to the public internet. If local Ollama is not installed or running, use the copy-prompt route with ChatGPT/Codex.

## Production choices

1. **Text package:** no-credit, primary route. Prepare the post, hook alternatives, visual brief, caption and CTA here.
2. **Still visual:** use OpenArt only after confirming that the selected model and mode are affordable; otherwise create a simple designed card or use an owned photograph.
3. **Motion video:** use owned phone footage plus FFmpeg/Blender. HeyGen's free plan is a short watermarked experiment, not the core dependency. OpenArt video is not available within the connected 25-credit balance.
4. **Publish:** human reviews the exact final post, then uses a connected scheduler or native app. Never treat a credit limit as a reason to abandon the content project.

## Official references

- Ollama Linux and quickstart: <https://github.com/ollama/ollama> and <https://github.com/ollama/ollama/blob/main/docs/quickstart.mdx>
- Qwen3 4B model size and Apache 2.0 licence: <https://ollama.com/library/qwen3:4b> and <https://github.com/QwenLM/Qwen3>
- Ollama local API and CORS configuration: <https://github.com/ollama/ollama/blob/main/docs/api/introduction.mdx> and <https://github.com/ollama/ollama/blob/main/docs/faq.mdx>
- HeyGen pricing: <https://www.heygen.com/pricing>
- OpenArt pricing and free-trial FAQ: <https://openart.ai/suite/pricing> and <https://openart.ai/faq/>
- GitHub Actions billing: <https://docs.github.com/en/actions/concepts/billing-and-usage>
