#!/usr/bin/env bash
# One-time (re-runnable) setup for YOLTServer: Java 25, Fabric for 26.3, mods from mods.txt.
set -euo pipefail
cd "$(dirname "$0")"

MC_VERSION="${MC_VERSION:-26.3}"
LOADER_VERSION="${LOADER_VERSION:-0.20.1}"
INSTALLER_VERSION="${INSTALLER_VERSION:-1.1.2}"
JAVA_MAJOR_REQUIRED=25

say() { printf '\n== %s\n' "$*"; }
die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

# ---------- 1. Java 25 ----------
java_major() {
  local bin=$1
  "$bin" -version 2>&1 | sed -n 's/.*version "\([0-9]*\).*/\1/p' | head -1
}

say "Resolving Java ${JAVA_MAJOR_REQUIRED}+"
JAVA_BIN=""
if command -v java >/dev/null 2>&1; then
  m=$(java_major java) || m=""
  if [ -n "${m:-}" ] && [ "$m" -ge "$JAVA_MAJOR_REQUIRED" ]; then
    JAVA_BIN=$(command -v java)
    echo "Using system java ($("$JAVA_BIN" -version 2>&1 | head -1))"
  else
    echo "System java is ${m:-absent}; need ${JAVA_MAJOR_REQUIRED}+"
  fi
fi

if [ -z "$JAVA_BIN" ]; then
  if [ -x ./java/bin/java ] && [ "$(java_major ./java/bin/java)" -ge "$JAVA_MAJOR_REQUIRED" ]; then
    JAVA_BIN=./java/bin/java
    echo "Using bundled ./java"
  else
    echo "Downloading Temurin ${JAVA_MAJOR_REQUIRED} into ./java"
    arch=$(uname -m)
    case "$arch" in
      x86_64) a=x64 ;;
      aarch64|arm64) a=aarch64 ;;
      *) die "unsupported architecture: $arch" ;;
    esac
    tmp=$(mktemp -d)
    curl -fsSL -A "YOLTServer-setup/1.0" \
      -o "$tmp/jdk.tar.gz" \
      "https://api.adoptium.net/v3/binary/latest/${JAVA_MAJOR_REQUIRED}/ga/linux/${a}/jdk/hotspot/normal/eclipse" \
      || die "JDK download failed"
    mkdir -p "$tmp/x"
    tar xzf "$tmp/jdk.tar.gz" -C "$tmp/x"
    jdkdir=$(find "$tmp/x" -maxdepth 1 -mindepth 1 -type d | head -1)
    rm -rf ./java ./jdk-*/
    mv "$jdkdir" ./java
    rm -rf "$tmp"
    JAVA_BIN=./java/bin/java
    echo "Installed $("$JAVA_BIN" -version 2>&1 | head -1)"
  fi
fi

# ---------- 2. Fabric server ----------
if [ ! -f fabric-server-launch.jar ]; then
  say "Installing Fabric Loader ${LOADER_VERSION} on Minecraft ${MC_VERSION}"
  if [ ! -f fabric-installer.jar ]; then
    curl -fsSL -o fabric-installer.jar \
      "https://maven.fabricmc.net/net/fabricmc/fabric-installer/${INSTALLER_VERSION}/fabric-installer-${INSTALLER_VERSION}.jar" \
      || die "fabric-installer download failed"
  fi
  "$JAVA_BIN" -jar fabric-installer.jar server \
    -mcversion "$MC_VERSION" -loader "$LOADER_VERSION" -downloadMinecraft -dir .
else
  say "Fabric already installed (fabric-server-launch.jar present)"
fi

# ---------- 3. Mods ----------
say "Fetching mods"
python3 fetch_mods.py

# ---------- 4. EULA ----------
if [ "$*" != "" ] && printf '%s\n' "$*" | grep -q -- '--accept-eula'; then
  printf 'eula=true\n' > eula.txt
  echo "eula.txt: accepted (https://aka.ms/MinecraftEULA)"
elif [ ! -f eula.txt ]; then
  printf 'eula=false\n' > eula.txt
  echo "eula.txt created with eula=false — set it to true (or rerun with --accept-eula) to start."
fi

say "Done"
echo "Start the server with: ./start.sh"
