FROM mcr.microsoft.com/devcontainers/base:noble

ARG GODOT_VERSION=4.6.3

USER root

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      libfontconfig1 \
      ca-certificates \
      curl \
      unzip \
      python3 \
 && rm -rf /var/lib/apt/lists/*

# Godot engine binary
RUN curl -sSL -o /tmp/godot.zip \
      "https://github.com/godotengine/godot/releases/download/${GODOT_VERSION}-stable/Godot_v${GODOT_VERSION}-stable_linux.x86_64.zip" \
 && mkdir -p /opt/godot \
 && unzip -q /tmp/godot.zip -d /opt/godot \
 && mv "/opt/godot/Godot_v${GODOT_VERSION}-stable_linux.x86_64" /opt/godot/godot \
 && chmod +x /opt/godot/godot \
 && ln -sf /opt/godot/godot /usr/local/bin/godot \
 && rm /tmp/godot.zip

# Web export templates only (full templates archive is ~1.2 GB; web bits are ~38 MB)
RUN curl -sSL -o /tmp/templates.tpz \
      "https://github.com/godotengine/godot/releases/download/${GODOT_VERSION}-stable/Godot_v${GODOT_VERSION}-stable_export_templates.tpz" \
 && mkdir -p "/home/vscode/.local/share/godot/export_templates/${GODOT_VERSION}.stable" \
 && unzip -j /tmp/templates.tpz \
      "templates/web_release.zip" \
      "templates/web_nothreads_release.zip" \
      "templates/web_debug.zip" \
      "templates/web_nothreads_debug.zip" \
      "templates/version.txt" \
      -d "/home/vscode/.local/share/godot/export_templates/${GODOT_VERSION}.stable" \
 && chown -R vscode:vscode /home/vscode/.local \
 && rm /tmp/templates.tpz

USER vscode
