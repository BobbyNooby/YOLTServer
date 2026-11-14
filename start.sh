#!/usr/bin/env bash
# Start YOLTServer. Prefers ./java (bundled by setup.sh), falls back to system java.
set -euo pipefail
cd "$(dirname "$0")"

if [ -x ./java/bin/java ]; then
  JAVA=./java/bin/java
else
  JAVA=$(command -v java) || { echo "no java found — run ./setup.sh first" >&2; exit 1; }
fi

HEAP="${SERVER_HEAP:-3G}"
if [ -f eula.txt ] && ! grep -q '^eula=true' eula.txt; then
  echo "eula.txt is not accepted — run ./setup.sh --accept-eula" >&2
  exit 1
fi

exec "$JAVA" \
  -Xms1G -Xmx"$HEAP" \
  -XX:+UseG1GC \
  -XX:+ParallelRefProcEnabled \
  -XX:MaxGCPauseMillis=200 \
  --enable-native-access=ALL-UNNAMED \
  -jar fabric-server-launch.jar nogui
