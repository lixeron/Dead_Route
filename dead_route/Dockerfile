FROM python:3.12-slim

LABEL maintainer="Dead Route Dev Team"
LABEL description="Dead Route - A Zombie Survival Roguelite"
LABEL version="0.12.0"

# No external dependencies - stdlib only (sqlite3, json, random, etc.)
# This keeps the image tiny

WORKDIR /app

COPY dead_route/ ./dead_route/

# Create audio directories (game runs silently in Docker - no audio player)
RUN mkdir -p dead_route/audio/music dead_route/audio/sfx

# Non-root user for security best practice
RUN useradd -m -s /bin/bash player
USER player

WORKDIR /app/dead_route

# Interactive terminal required for gameplay
ENTRYPOINT ["python3", "main.py"]
