#!/usr/bin/env bash
set -euo pipefail
cd /opt/pitchclipers
git pull --ff-only origin main
docker rm -f pitchclipers 2>/dev/null || true
docker build -t pitchclipers:latest .
docker run -d --name pitchclipers --restart unless-stopped -p 80:8000 pitchclipers:latest
