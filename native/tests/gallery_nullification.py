"""What the committed nullification contract strikes from the Gallery library, for the gates that pin that library.

The Gallery builders omit every recipe the operator's contract (native/contract/NULLIFICATION.json) strikes, through
build_gallery.nullifiedRecipes (native/docs/NULLIFICATION.md). A gate that pins the size of the built library, its
attract rotation or a particular recipe holds that pin for what the contract leaves: the operator using the mechanism
does not turn it red, and a Gallery that keeps a struck recipe still fails it. committed() resolves the contract at the
repository's default path with native/scripts/nullification.py, the module the builders use, against the library
apply_nullification.gallery_library assembles as build_gallery.py does (native/recipes.json, then the generated
studies). It needs neither the inventory nor native/evidence, so it runs in an extracted SDK.

Tests load this file by its path, because they run both from native/tests and as tests.<module> from native. Run as a
script, it writes {"struck": [ids], "library": [recipes] or null} to the path given, for the Node gates.
"""
import json
import sys
from pathlib import Path

NATIVE = Path(__file__).resolve().parents[1]


def committed(native=NATIVE):
    """(library, struck): the Gallery library before the committed contract applies and the ids of the recipes the
    contract strikes from it. When it strikes no Gallery recipe, struck is empty and library is None, and the gates keep
    their complete-library pins."""
    native = Path(native)
    scripts = str(native / 'scripts')
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    import nullification
    import gallery_provenance
    import apply_nullification
    resolved = nullification.load_contract(native.parent)
    library = apply_nullification.gallery_library(native.parent)
    # Provenance admission (native/contract/GALLERY-ADMISSION.json) runs before nullification in build_gallery: an
    # entry the ledger does not admit is absent from the Gallery exactly as a struck one is.
    admitted = set(gallery_provenance.admitted_ids(native / 'contract/GALLERY-ADMISSION.json'))
    struck = frozenset(nullification.gallery_strikes(library, resolved) if resolved else ()) | frozenset(
        r['id'] for r in library if r['id'] not in admitted)
    return (library if struck else None), struck


if __name__ == '__main__':
    try:
        library, struck = committed()
    except ValueError as error:
        raise SystemExit(str(error)) from None
    Path(sys.argv[1]).write_text(json.dumps({'struck': sorted(struck), 'library': library}, separators=(',', ':')),
                                 encoding='utf-8')
