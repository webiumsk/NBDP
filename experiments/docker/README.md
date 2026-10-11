# Source-pinned local relay environment

Both relays are independent actual implementations, with disposable storage and an internal Docker network. The loopback TCP proxy forwards bytes; it does not act as a relay. Docker must be accessible, Node 22.18.0 installed, and ports 17777/18081 free. No public relay is contacted.

## Build

Run from `experiments/`, after reading the candidate contract. These are the exact source pins used:

```sh
git clone https://github.com/hoytech/strfry.git /tmp/nbdp-005-strfry
git -C /tmp/nbdp-005-strfry checkout 4cd3cf64850caf47dda46c2a2abbbf3525a64d10
docker build -f "$PWD/docker/Dockerfile.strfry" -t nbdp-005-strfry:4cd3cf6 /tmp/nbdp-005-strfry
git clone https://github.com/scsibug/nostr-rs-relay.git /tmp/nbdp-005-rs-relay
git -C /tmp/nbdp-005-rs-relay checkout b5c1f642e4f4c3b9c54f5d18d66f4c53642076b4
docker build -f "$PWD/docker/Dockerfile.rs-relay" -t nbdp-005-rs-relay:b5c1f64 /tmp/nbdp-005-rs-relay
```

Dockerfiles pin base image digests and require the exact Git HEAD. Rust uses the upstream Cargo lock. Submodule revisions and Debian package inventories are retained in [results](../results/). APT uses current package indices: rebuilding is source/lock controlled, **not bit-for-bit guaranteed**. Tested image IDs are in the [environment manifest](../results/environment.json); matching those artifacts reproduces the captured binaries. Do not equate image build success with transport interoperability.

## Run

```sh
bash docker/start.sh
```

Keep this terminal running; run experiments from another terminal. The script fails on an existing network/container name and manages no unrelated container. It starts read-only roots, UID/GID-local writers, 1 GiB RAM, 2 CPUs and 128 process limits. Persistent databases exist only under ignored `.runtime/`. Bind addresses inside containers are private; proxy listeners bind **127.0.0.1 only**. Tests explicitly whitelist these endpoints. The original run also specified loopback Docker port bindings, but this daemon's internal network omitted NAT; reproduction uses the observed explicit proxy path.

strfry max event = 65,536 bytes and WebSocket payload = 131,072; rs-relay max event/frame policy = 32,768 with WebSocket caps 131,072. Exact normalized-event versus frame behavior is **not validated until E04 executes**. AUTH and restricted-kind reads are explicitly disabled in this synthetic lab; their production privacy/support implications remain E10/E15. The initial E02 config left restricted reads enabled despite disabling AUTH: events were accepted but inaccessible to the unauthenticated reader. That failed result is preserved and explained in [E02](../results/E02.md).

Stop only the two named lab containers and network:

```sh
# First stop the proxy with Ctrl-C in its terminal.
docker stop nbdp-005-strfry nbdp-005-rs-relay
docker rm nbdp-005-strfry nbdp-005-rs-relay
docker network rm nbdp-005-lab
```

Delete disposable databases only after preserving needed evidence, using your normal local file management. No relay is modified outside this named lab. Ten-day retention and seven-day recovery are not configured/proven by starting these processes.
