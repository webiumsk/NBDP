#!/bin/sh
set -eu
umask 077
printf 'BUILD_SCOPE=COMPILE_BOOTSTRAP_ONLY_NO_NATIVE_EXECUTION\n'
id
rustc --version --verbose
cargo --version --verbose
rustup show active-toolchain
printf 'CARGO_BUILD_START\n'
cargo build --locked --manifest-path /src/Cargo.toml --target-dir /target
printf 'CARGO_BUILD_FINISHED\n'
