use std::{env, fs, path::PathBuf, process::Command};
fn main() {
    let root = PathBuf::from(env::var_os("CARGO_MANIFEST_DIR").unwrap()).join("../..");
    let output = PathBuf::from(env::var_os("OUT_DIR").unwrap());
    println!("cargo:rerun-if-env-changed=NOCTURNE_COVERAGE");
    if env::var("NOCTURNE_COVERAGE").as_deref() == Ok("1") {
        // Share the measured C core with Python and Go during qualification.
        // Normal SDK consumers still receive the independently built archive.
        let dist = root.join("dist").canonicalize().expect("qualified native dist");
        let library = if cfg!(target_os = "macos") { "libnocturne_native.dylib" }
                      else { "libnocturne_native.so" };
        assert!(dist.join(library).is_file(), "coverage core must be built first");
        println!("cargo:rerun-if-changed={}", dist.join(library).display());
        println!("cargo:rustc-link-search=native={}", dist.display());
        println!("cargo:rustc-link-lib=dylib=nocturne_native");
        println!("cargo:rustc-link-arg=-Wl,-rpath,{}", dist.display());
        return;
    }

    let cc = env::var_os("CC").unwrap_or_else(|| "cc".into());
    let ar = env::var_os("AR").unwrap_or_else(|| "ar".into());
    let mut sources: Vec<_> = fs::read_dir(root.join("src")).unwrap().map(|x|x.unwrap().path())
        .filter(|p|p.extension().map(|x|x=="c").unwrap_or(false) && p.file_name().unwrap()!="wasm_mem.c").collect();
    sources.sort();
    let mut objects = Vec::new();
    for source in sources {
        println!("cargo:rerun-if-changed={}",source.display());
        let object = output.join(source.file_stem().unwrap()).with_extension("o");
        let status=Command::new(&cc).args(["-std=c11","-O2","-ffp-contract=off","-fno-fast-math","-fno-strict-aliasing","-fPIC"])
            .arg("-I").arg(root.join("include")).arg("-I").arg(root.join("src"))
            .arg("-c").arg(&source).arg("-o").arg(&object).status().expect("run native C compiler");
        assert!(status.success(),"C compilation failed: {}",source.display());
        objects.push(object);
    }
    // Source ports carry companion headers and tables. Any included data change
    // must invalidate the static archive just as a C implementation change does.
    for directory in ["include", "src"] {
        println!("cargo:rerun-if-changed={}",root.join(directory).display());
        for entry in fs::read_dir(root.join(directory)).unwrap() {
            let path = entry.unwrap().path();
            if matches!(path.extension().and_then(|x| x.to_str()), Some("h" | "inc")) {
                println!("cargo:rerun-if-changed={}",path.display());
            }
        }
    }
    let archive=output.join("libnocturne_native.a");
    let _=fs::remove_file(&archive);
    assert!(Command::new(ar).arg("crs").arg(&archive).args(objects).status().expect("run ar").success());
    println!("cargo:rustc-link-search=native={}",output.display());
    println!("cargo:rustc-link-lib=static=nocturne_native");
    println!("cargo:rerun-if-env-changed=CC");println!("cargo:rerun-if-env-changed=AR");
}
