ARG PYTHON_IMAGE=registry-1.docker.io/library/python:3.11-slim@sha256:e88e9763f943ec1834f992a4b51e0f24500486803e8bc534e5767af9ea65f6ce
FROM ${PYTHON_IMAGE}
ARG DEBIAN_FRONTEND=noninteractive
ENV container=docker

WORKDIR /app

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:${PATH}" \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    ffmpeg \
    default-libmysqlclient-dev \
    pkg-config \
    libvulkan1 \
    mesa-vulkan-drivers \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash appuser

COPY requirements.lock .
RUN python -m venv "$VIRTUAL_ENV"
RUN pip install --no-cache-dir --require-hashes -r requirements.lock

COPY --chown=appuser:appuser . .

EXPOSE 8000

USER appuser

CMD ["python", "docker_entrypoint.py", "daphne", "-b", "0.0.0.0", "-p", "8000", "config.asgi:application"]
