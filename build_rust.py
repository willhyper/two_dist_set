"""Opt-in source/editable-install native build: python build_rust.py [--debug].

Normal pip installs remain pure Python. No third-party Rust crates are needed.
Re-run for each target OS/architecture; restart Python to select the new library.
"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys


def build(debug=False):
    root = Path(__file__).resolve().parent
    cargo = shutil.which('cargo')
    if cargo is None:
        candidate = Path.home() / '.cargo' / 'bin' / ('cargo.exe' if os.name == 'nt' else 'cargo')
        if candidate.exists():
            cargo = str(candidate)
    if cargo is None:
        raise SystemExit('Rust is not installed. Install it from https://rustup.rs and retry.')
    manifest = root / 'rust' / 'canon' / 'Cargo.toml'
    command = [cargo, 'build', '--locked', '--manifest-path', str(manifest)]
    if not debug:
        command.append('--release')
    subprocess.run(command, check=True)
    filename = ('srg_canon.dll' if sys.platform == 'win32' else
                'libsrg_canon.dylib' if sys.platform == 'darwin' else 'libsrg_canon.so')
    suffix = Path(filename).suffix
    target = Path(os.environ.get('CARGO_TARGET_DIR', root / 'rust' / 'canon' / 'target'))
    source = target / ('debug' if debug else 'release') / filename
    destination = root / 'src' / 'srg' / ('_canon_rust' + suffix)
    temporary = destination.with_suffix(suffix + '.tmp')
    shutil.copyfile(source, temporary)
    temporary.replace(destination)
    print(destination)
    return destination


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--debug', action='store_true')
    build(parser.parse_args().debug)
