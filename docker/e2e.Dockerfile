FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    python3.11 python3.11-venv python3-pip build-essential curl wget ca-certificates git \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdbus-1-3 libdrm2 libxkbcommon0 \
    libxcomposite1 libxrandr2 libgdk-pixbuf2.0-0 libxrender1 libxss1 libasound2 libxdamage1 libgbm1 libwebp-dev libffi-dev \
  && rm -rf /var/lib/apt/lists/*

RUN useradd -ms /bin/bash runner
WORKDIR /home/runner/app
COPY --chown=runner:runner . /home/runner/app

USER runner
ENV PATH="/home/runner/app/venv/bin:$PATH"

RUN python3.11 -m venv venv && \
    . venv/bin/activate && \
    pip install --upgrade pip setuptools wheel && \
    pip install --prefer-binary -r requirements.txt && \
    # Install Playwright browsers and system deps (on Ubuntu image this will use apt)
    playwright install --with-deps || true

CMD bash -lc \
  "export MOCK_CDX=true && . venv/bin/activate && ./launch_app.sh & sleep 4 && pytest tests/e2e -q"
