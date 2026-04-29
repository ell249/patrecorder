#!/bin/bash
# PAT Recorder — Docker start script
#
# Build the image first (re-run after any code change):
#   docker build -f Dockerfile.example -t patrecorder .

# Ensure host-side upload directories exist before bind-mounting.
# If they don't exist Docker creates them as root, which causes permission errors.
mkdir -p static/uploads/tests static/uploads/repairs

# Auto-create config.py from the example template on first run.
# The in-browser setup wizard will write the real DB credentials into this file.
[ -f config.py ] || cp config.example.py config.py

docker run -d \
  -p 5090:5090 \
  --restart unless-stopped \
  --name patrecorder \
  -v "$PWD/config.py:/app/config.py" \
  -v "$PWD/static/uploads:/app/static/uploads" \
  patrecorder
