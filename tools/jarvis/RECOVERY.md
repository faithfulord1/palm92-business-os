# Faithful Jarvis recovery

Recovered 17 October 2026 from the existing Startup Repair package.

The Python prompt contained an unescaped apostrophe and could not parse. This
copy corrects it. `start-jarvis.ps1` tries installed Python runtimes, including
Blender's bundled Python, before giving up. It skips the broken WindowsApps alias.
No installation, paid API or third-party Python package is required.

Run `./start-jarvis.ps1` from PowerShell. If Windows blocks scripts, do not disable
security controls: invoke an installed Python executable with `local_server.py`
directly. `PALM92_PYTHON` can select the executable explicitly.

Verification: `python -m unittest -v test_server.py` tests model reporting,
offline errors, origin and host restrictions, blank input and the chat contract
without accessing real accounts or a model. A live model reply is a separate check.

The assistant still has drafting desks, browser-local memory and task tracking.
It does not have email/LinkedIn sending or unattended monitoring. Those must not
be marked completed until a real authorised connector and delivery receipt work.

Ollama must run locally, and a model must already be installed. The server binds
only to 127.0.0.1:4700. Model requests go to 127.0.0.1:11434.
