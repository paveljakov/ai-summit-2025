# AI Summit 2025 CLI - Docker Container
#
# Includes: Python 3.13, Git, Java 21 (OpenJDK LTS), Maven
#
# Build:
#   docker build -t aisummit-cli .
#
# Usage:
#   1. Interactive demo shell (recommended for demos):
#      docker compose run demo
#      # Inside container: aisummit, git, java, mvn available system-wide
#      aisummit "your query"
#      java -version
#      mvn --version
#      cd /workspace && git status
#
#   2. Run aisummit directly:
#      docker compose run cli "your query here"
#
#   3. Interactive shell without compose:
#      docker run -it --rm --env-file .env \
#        -v $(pwd):/workspace:ro -w /workspace \
#        --entrypoint /bin/bash aisummit-cli
#
#   4. Direct query without compose:
#      docker run -it --rm --env-file .env aisummit-cli "query"

FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    locales \
    openjdk-21-jdk \
    maven \
    && rm -rf /var/lib/apt/lists/*

# Set Java environment variables
ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-arm64
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# Configure locale for Unicode support (critical for Textual box drawing)
RUN sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8

# Install Poetry
RUN pip install poetry==1.8.0

# Copy Poetry configuration (include lock file for reproducible builds)
COPY pyproject.toml poetry.lock* ./

# Configure Poetry to not create a virtual environment (we're already in a container)
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-interaction --no-ansi --no-root

# Copy application code
COPY src/ ./src/
COPY CLAUDE.md README.md ./

# Install the package
RUN poetry install --no-interaction --no-ansi

# Set workspace directory
WORKDIR /workspace

# Create a non-root user for security
RUN useradd -m -u 1000 aisummit && \
    chown -R aisummit:aisummit /app /workspace
USER aisummit

# Set environment variables for optimal TUI experience
ENV PYTHONUNBUFFERED=1
ENV TERM=xterm-256color
ENV COLORTERM=truecolor

# Use ENTRYPOINT + CMD pattern for better argument handling
# This allows: docker run -it aisummit-cli "your query here"
ENTRYPOINT ["aisummit"]
CMD []
