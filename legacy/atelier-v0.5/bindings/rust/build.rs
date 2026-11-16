//! Compile the shared C kernel without adding a Cargo build dependency.
//! Native POSIX hosts are supported by this bootstrap build script.
use std::{env, path::PathBuf, process::Command};

fn main() {
    let host = env::var("HOST").expect("HOST");
    let target = env::var("TARGET").expect("TARGET");
    assert!(host == target, "Cross compilation requires an explicit target C toolchain; this bootstrap build supports native hosts only");
    assert!(!target.contains("windows"), "Use the WASM binding on Windows; this native build script targets POSIX");
    println!("cargo:rerun-if-env-changed=CC");
    println!("cargo:rerun-if-env-changed=AR");
    let root = PathBuf::from(env::var("CARGO_MANIFEST_DIR").expect("manifest directory"));
    let sourceRoot = root.join("../..");
    let out = PathBuf::from(env::var("OUT_DIR").expect("Cargo output directory"));
    let object = out.join("nocturne.o");
    let compiler = env::var("CC").unwrap_or_else(|_| "cc".into());
    let archiver = env::var("AR").unwrap_or_else(|_| "ar".into());
    let status = Command::new(compiler)
        .args(["-std=c11", "-O3", "-fPIC", "-c"])
        .arg(sourceRoot.join("src/nocturne.c"))
        .arg("-I").arg(sourceRoot.join("include"))
        .arg("-o").arg(&object)
        .status().expect("C compiler must be installed");
    assert!(status.success(), "C renderer compilation failed");
    let status = Command::new(archiver).arg("crs")
        .arg(out.join("libnocturne.a")).arg(&object)
        .status().expect("archiver must be installed");
    assert!(status.success(), "renderer archive failed");
    println!("cargo:rustc-link-search=native={}", out.display());
    println!("cargo:rustc-link-lib=static=nocturne");
    for file in ["src/nocturne.c", "src/ok_color.inc", "src/ok_tables.inc", "src/defaults.inc", "src/sine.inc", "include/nocturne.h", "src/studio.inc", "src/studio_widgets.inc", "src/studio_defaults.inc", "include/nocturne_studio.h"] {
        println!("cargo:rerun-if-changed={}", sourceRoot.join(file).display());
    }
}
