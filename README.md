<div align="center">
  <a href="https://www.pixiv.net/en/artworks/130821036">
    <img src="https://i.imgur.com/WvyRtdu.png" alt="Illustration by Arren">
  </a>
  <p>Art by Arren</p>
  <h1>Ugoku-v2 Discord Bot</h1>
</div>

Ugoku-v2 is a Discord bot with music, voice, chatbot, and utility features.
This repository is a fork and rework of
[Shewiiii/Ugoku-bot](https://github.com/Shewiiii/Ugoku-bot), not the original
Ugoku project.

**Thank you to [Shewiiii](https://github.com/Shewiiii) for the original
Ugoku-bot project and the foundation this fork continues to build on.**

Current repository:

- GitHub: [Melivo/Ugoku-v2](https://github.com/Melivo/Ugoku-v2)

## Features

- Discord slash commands for music playback and voice queues.
- Spotify playback through Librespot and the Spotify Web API, including playlist
  support and complete playlist pagination.
- Optional Deezer playback and download commands for Spotify and Deezer.
- Lyrics, queue management, audio effects, and custom audio sources.
- Optional Gemini chatbot with history and Google Search; OpenAI and Pinecone
  integrations can be enabled when needed.
- Translation, JPDB vocabulary lookup, Danbooru search, and other utility
  commands.
- Restricted `/health` command for server administrators and systemd-based
  production monitoring.

## Requirements

- Python 3.12.x or 3.13.x
- FFmpeg available on `PATH`
- A Discord bot token
- Credentials for enabled integrations, such as Spotify, Deezer, Gemini,
  Pinecone, OpenAI, Imgur, or Musixmatch

All environment variables are documented in [`.env.template`](.env.template).
Real credentials belong only in a local `.env` file and must never be committed.

## Local Setup

1. Clone the repository and enter the project directory.
2. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   # Windows PowerShell
   .\venv\Scripts\Activate.ps1
   # Linux/macOS
   source venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Copy `.env.template` to `.env` and set only the values needed for the
   enabled services.
5. Adjust feature switches in [`config.py`](config.py).
6. Create a Discord application and bot in the
   [Discord Developer Portal](https://discord.com/developers/applications),
   invite it to the target server, then start the bot:

   ```bash
   python main.py
   ```

7. When Spotify playback is enabled, select the Librespot device in the Spotify
   app. This creates `credentials.json` locally. It is sensitive and must never
   be committed.

## Production

The systemd units are located in [`deploy/`](deploy/). The primary service uses
a watchdog and restarts on failure. The health timer checks gateway,
slash-command, audio, and Spotify readiness, event-loop lag, and blocked
resources.

The legacy Linux host requires the CPU-compatible NumPy version:

```bash
pip install -r requirements.txt -c deploy/constraints-linux-legacy-cpu.txt
python -c "import numpy; assert numpy.__version__ == '2.1.3'"
```

The complete installation, deployment, recovery, and healthcheck procedure is
documented in
[`docs/runbooks/bot-produktionsueberwachung.md`](docs/runbooks/bot-produktionsueberwachung.md).

## Configuration

- [`.env.template`](.env.template): environment-variable names and optional
  integrations.
- [`config.py`](config.py): feature switches and runtime configuration.
- [`deploy/`](deploy/): systemd units, healthcheck timer, and legacy CPU
  constraint.

## License

This project is licensed under the [GNU GPL v3](LICENSE). Observe the license
terms of the original project and all included dependencies.
