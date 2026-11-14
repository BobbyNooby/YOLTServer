# YOLTServer

Server deployment for **You Only Live Twice** — Minecraft **26.3**, **Fabric Loader 0.20.1**,
Java **25**.

This repo is the config, not the binaries. Clone it on any machine, run `./setup.sh`, and you have
the same server: same `server.properties`, same mod set, same start script. The game server, the
JDK, the Fabric libraries and the world are all gitignored and regenerated/fetched by the scripts.

The gameplay mod itself lives in **[BobbyNooby/youonlylivetwice](https://github.com/BobbyNooby/youonlylivetwice)**.
Its release jars are what `mods.txt` pulls in — publish a new release there, bump the tag here,
re-run `./fetch_mods.py`, and every machine is in sync.

## Requirements

- Minecraft **26.3** requires **Java 25**. `setup.sh` uses your system Java if it is 25+, otherwise
  it downloads Temurin 25 into `./java` (no root needed).
- `bash`, `curl`, `python3` (stdlib only — used for the Modrinth/GitHub API calls).

## First install

```bash
git clone https://github.com/BobbyNooby/YOLTServer.git
cd YOLTServer
./setup.sh --accept-eula     # drop --accept-eula to write eula.txt=false and accept later
./start.sh
```

`setup.sh` does four things: resolves Java 25, runs the Fabric installer for 26.3 + loader 0.20.1,
downloads the mods listed in `mods.txt`, and writes `eula.txt` if it is missing.

## Day to day

| Task | Command |
|---|---|
| Update mods to latest 26.3 builds | `./fetch_mods.py` |
| Update the server config | `git pull` |
| Start | `./start.sh` |
| Sync a mod set to another PC | `git pull && ./fetch_mods.py` |
| Change Minecraft/Fabric/Java version | edit the versions at the top of `setup.sh`, re-run it |

Mods are downloaded, never committed. `mods.txt` holds the list:

```
# modrinth:<slug>[@<version>]      newest (or pinned) Fabric build for 26.3
# github:<owner>/<repo>[@<tag>]    .jar asset from that GitHub release

modrinth:fabric-api
github:BobbyNooby/youonlylivetwice@v1.0.0
```

Pin with `@<version>` (`modrinth:fabric-api@0.166.2+26.3`) or leave it off to always take the
newest stable build. Every download is verified against the sha512 the API reports.

## Running as a service

`systemd/YOLTServer.service` runs it under systemd with restart-on-crash:

```bash
sudo cp systemd/YOLTServer.service /etc/systemd/system/
sudo systemctl enable --now YOLTServer
journalctl -u YOLTServer -f
```

Edit `User=` and `WorkingDirectory=` in the unit first. Stop the server with
`sudo systemctl stop YOLTServer` — never `kill -9`, that can clip a world save.

## Ports

`25565/tcp`, bound to all interfaces (`server-ip=`). That is LAN + Tailscale by default. Exposing it
to the public internet needs a router port-forward and is a deliberate choice, not a default.

## Memory

`start.sh` allocates `-Xms1G -Xmx3G`. Override with `SERVER_HEAP`:

```bash
SERVER_HEAP=6G ./start.sh
```

## Not in this repo

`world/`, `logs/`, `libraries/`, `versions/`, `.fabric/`, the JDK, `server.jar` and the mod jars.
Worlds are player data — back them up separately, not in git.
