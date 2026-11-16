.PHONY: build gallery test browser demo tmux docs
build:
	sh scripts/build.sh --wasm
	tsc -p tsconfig.json
gallery: build
	python3 scripts/build_studio_gallery.py
test:
	sh scripts/check_studio.sh
browser: gallery
	python3 scripts/check_studio_browser.py
demo:
	python3 examples/studio_terminal.py
tmux:
	python3 tmux/preview.py --profile smart-dark
docs:
	@printf 'Start with README.md, docs/STUDIO_API.md and AGENTS.md\n'
