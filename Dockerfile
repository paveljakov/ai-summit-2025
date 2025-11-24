# AI Summit 2025 CLI - Docker Container
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==1.8.0

# Copy Poetry configuration
COPY pyproject.toml ./

# Configure Poetry to not create a virtual environment (we're already in a container)
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-interaction --no-ansi --no-root

# Copy application code
COPY src/ ./src/
COPY CLAUDE.md README.md ./

# Install the package
RUN poetry install --no-interaction --no-ansi

# Create a non-root user for security
RUN useradd -m -u 1000 aisummit && \
    chown -R aisummit:aisummit /app
USER aisummit

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV TERM=xterm-256color

# Default command
CMD ["aisummit"]
