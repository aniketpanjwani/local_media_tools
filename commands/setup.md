# Setup Environment

Initialize the newsletter tools environment.

## Instructions

1. Follow the `newsletter-events-setup` skill workflow
2. Run `scripts/setup.sh` to install dependencies
3. Verify API keys are configured in `.env`
4. Ensure `config/sources.yaml` exists with venue configuration
5. Report setup status

## What This Does

- Installs Python dependencies via `uv`
- Installs Node.js dependencies via `bun`
- Creates required directories
- Validates configuration

## After Setup

1. Copy `.env.example` to `.env` and add your API keys
2. Copy `config/sources.example.yaml` to `config/sources.yaml`
3. Edit `sources.yaml` to add your venues and accounts
