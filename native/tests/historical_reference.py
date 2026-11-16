"""Immutable original runtime input, portable across checkouts and CI hosts."""
from contextlib import contextmanager
import gzip
import hashlib
from pathlib import Path
import tempfile

RC2_HTML_SHA256 = '375c4468c886728bc790b8d8cc3bdddc2a046532a4d792cde190f1b522a66385'
RC2_ARCHIVE_SHA256 = '9280288a52737d2bfe54379627f5cbe8a280c939a3eece79a1be08eaa6041e63'
RC2_WASM_SHA256 = 'aa04c1705a5982b924d420971bfcbc7bbedd49f1ea527a9900531b61b0c92a09'
RC2_FIXTURE = Path(__file__).resolve().parent / 'fixtures/original-rc2-workbench-docs.html.gz'
RC2_ARCHIVE_FIXTURE = Path(__file__).resolve().parent / 'fixtures/original-rc2-gallery.zip'


def load_rc2_workbench(fixture=None):
    """Return exact original HTML; reject missing, corrupt or replaced bytes."""
    path = RC2_FIXTURE if fixture is None else Path(fixture)
    try:
        data = gzip.decompress(path.read_bytes())
        if len(data) != 875089 or hashlib.sha256(data).hexdigest() != RC2_HTML_SHA256:
            raise ValueError('Original RC2 HTML identity mismatch')
        return data.decode('utf-8')
    except (OSError, EOFError, UnicodeError) as error:
        raise ValueError(f'Cannot read original RC2 runtime fixture: {path}') from error


def load_rc2_archive(fixture=None):
    """Return the byte-exact RC2 archive and reject missing or altered custody."""
    path = RC2_ARCHIVE_FIXTURE if fixture is None else Path(fixture)
    try:
        data = path.read_bytes()
        if len(data) != 2835114 or hashlib.sha256(data).hexdigest() != RC2_ARCHIVE_SHA256:
            raise ValueError('Original RC2 archive identity mismatch')
        return data
    except OSError as error:
        raise ValueError(f'Cannot read original RC2 archive fixture: {path}') from error


@contextmanager
def rc2_workbench_file(fixture=None):
    """Yield a temporary standalone copy for actual browser and WASM tools."""
    source = load_rc2_workbench(fixture)
    with tempfile.TemporaryDirectory(prefix='nocturne-original-rc2-') as directory:
        path = Path(directory) / 'Nocturne-Workbench-Docs.html'
        path.write_bytes(source.encode('utf-8'))
        yield path
