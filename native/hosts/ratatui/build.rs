use std::{env, path::PathBuf};

fn main() {
    println!("cargo:rerun-if-env-changed=NOCTURNE_COVERAGE");
    if env::var("NOCTURNE_COVERAGE").as_deref() != Ok("1") {
        return;
    }
    // Dependency-local rustc-link-arg does not reach this package's final
    // executables. Measured hosts load the same qualified C image directly.
    let dist = PathBuf::from(env::var_os("CARGO_MANIFEST_DIR").unwrap())
        .join("../../dist").canonicalize().expect("qualified native dist");
    let library = if env::var("CARGO_CFG_TARGET_OS").as_deref() == Ok("macos") {
        "libnocturne_native.dylib"
    } else {
        "libnocturne_native.so"
    };
    assert!(dist.join(library).is_file(), "coverage core must be built first");
    println!("cargo:rerun-if-changed={}", dist.join(library).display());
    println!("cargo:rustc-link-arg=-Wl,-rpath,{}", dist.display());
}
