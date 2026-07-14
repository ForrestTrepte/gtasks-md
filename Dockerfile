FROM python:3.13-slim

# Build-time staging area for dependency installation.
# The dev container workspace is mounted or cloned separately at runtime.
WORKDIR /tmp/build

# Install curl, git, pandoc, and then clean up the cached package lists
RUN apt-get update && apt-get install -y curl git pandoc && rm -rf /var/lib/apt/lists/*

# Install Claude Code
RUN curl -fsSL https://claude.ai/install.sh | bash
ENV PATH="/root/.local/bin:${PATH}"
# Pre-seed onboarding state so the "let's get started" flow is skipped
RUN echo '{"hasCompletedOnboarding":true,"lastOnboardingVersion":"1.0.0","projects":{"/workspaces/WordSpace":{"hasTrustDialogAccepted":true}}}' > /root/.claude.json

# Install uv and package dependencies
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
# Create a virtual environment for the project outside of the workspace to avoid it being overwritten by the mounted repository
# When selecting the virtual environment in VS Code, enter this value:
ENV UV_PROJECT_ENVIRONMENT=/opt/venvs/python-docker-devcontainers
COPY pyproject.toml uv.lock* ./
COPY app ./app
RUN uv sync --extra dev
RUN rm -rf /tmp/build

WORKDIR /workspaces

CMD ["bash"]