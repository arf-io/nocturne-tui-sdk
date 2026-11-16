# Nocturne SDK

Nocturne renders animated terminal cells from a shared C11 scene. Its native bindings and WebAssembly build use the same commands, geometry, materials, clocks and input ownership. A cell contains a Unicode scalar, foreground RGB, background RGB and semantic identity.

Read the [SDK contract](Contract.md) for ownership, persistence and limits. Start with [Getting started](Getting-Started.md), then [Composition](Composition.md). The [component atlas](Components.md) shows each visible component family and its declared states. [Input and motion](Input-and-Motion.md) explains camera rigs, editable text and time. [Materials and rendering](Materials-and-Rendering.md) explains dot sampling and layered color.

| Integration | Reference |
|---|---|
| Caller-owned C memory and queries | [C](C.md) |
| Browser or Node WebAssembly | [WASM and TypeScript](WASM-TypeScript.md) |
| Python applications | [Python](Python.md) |
| Go and Bubble Tea | [Go](Go.md) |
| Rust and Ratatui | [Rust](Rust.md) |
| Canvas, DOM, input and accessibility | [Web integration](Web.md) |
| A graphical SDK implementation brief | [GUI SDK prompt](Nocturne-GUI-SDK-Prompt.md) |

The Markdown pages are the reference. The HTML and the language PDFs are built from them and from the component images. The [reference manifest](manifest.json) lists the chapter order. [Capture metadata](images/CAPTURES.json) lists each component state and its image.

[Command field reference](Commands.md) lists the current JSON operations and typed fields.

The [component catalogue](Catalogue.md) lists the native effects, except those hidden by the nullification contract. For each effect it gives the commands that accept it, their parameters with defaults and domains, and examples the library accepts and refuses.

## Build the reference

The documentation builder needs Python 3.12 or later and the packages in [requirements.txt](requirements.txt). From the SDK root, create a separate environment and build the HTML and all nine PDFs:

```sh
python3 -m venv .venv-docs
.venv-docs/bin/python -m pip install -r docs/current/requirements.txt
.venv-docs/bin/python native/scripts/build_reference_docs.py --check
.venv-docs/bin/python native/scripts/build_reference_docs.py --output docs-reference
```

Open `docs-reference/README.html` for chapter and PDF links. `BUILD.json` lists the hashes of the Markdown, the input assets and the generated files. The build uses the component images in `docs/current/images` and checks them against their capture manifest.

## Run the tests

From the SDK root:

```sh
sh qualify-native.sh --profile rc2 --strict --capture --list
sh qualify-native.sh --profile rc2 --strict --capture
```

The run writes a report of the steps it ran.
