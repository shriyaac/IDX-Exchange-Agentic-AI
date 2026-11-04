# OpenClaw image + the Python libraries from the handbook (Week 0 pip install line).
# Python 3 is already in the OpenClaw image; this adds pip and the packages.
FROM ghcr.io/openclaw/openclaw:latest
USER root
RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends python3-pip \
 && rm -rf /var/lib/apt/lists/* \
 && python3 -m pip install --no-cache-dir --break-system-packages \
      pandas numpy sqlalchemy mysql-connector-python scikit-learn openai
USER node
