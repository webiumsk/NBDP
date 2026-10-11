#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")/.."
# Only new, explicitly named lab containers; Docker refuses occupied names.
mkdir -p .runtime/strfry .runtime/rs-relay
docker network create --internal nbdp-005-lab
docker run -d --name nbdp-005-strfry --network nbdp-005-lab --user "$(id -u):$(id -g)" --cpus 2 --memory 1g --pids-limit 128 --read-only --tmpfs /tmp --mount "type=bind,src=$PWD/docker/strfry.conf,dst=/src/strfry.conf,readonly" --mount "type=bind,src=$PWD/.runtime/strfry,dst=/data" nbdp-005-strfry:4cd3cf6 relay
docker run -d --name nbdp-005-rs-relay --network nbdp-005-lab --user "$(id -u):$(id -g)" --cpus 2 --memory 1g --pids-limit 128 --read-only --tmpfs /tmp --mount "type=bind,src=$PWD/docker/rs-relay.toml,dst=/src/config.toml,readonly" --mount "type=bind,src=$PWD/.runtime/rs-relay,dst=/data" nbdp-005-rs-relay:b5c1f64 --db /data
docker inspect nbdp-005-strfry nbdp-005-rs-relay > .runtime/containers.json
python3 - <<'PY'
import json
from pathlib import Path
v=json.loads(Path('.runtime/containers.json').read_text())
ips={x['Name'].removeprefix('/nbdp-005-'):x['NetworkSettings']['Networks']['nbdp-005-lab']['IPAddress'] for x in v}
Path('.runtime/relay-ips.json').write_text(json.dumps(ips))
PY
# Internal network blocks outbound traffic. Host NAT may be omitted; explicit
# loopback forwarding does not parse or emulate relay protocol behavior.
node docker/proxy.mjs
