#!/usr/bin/env python3
"""Expand user-selected fixtures and run each independently."""
import base64
import glob
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

root = Path(__file__).resolve().parent.parent
out = Path(os.environ['OUTPUT_DIR']).resolve()
out.mkdir(parents=True, exist_ok=True)
setup = json.loads((out / 'setup_receipt.json').read_text())
os.environ['SETUP_STATUS'] = setup['setup_status']
patterns = shlex.split(os.environ.get('FIXTURES', '') or 'fixtures/public/core1/*.lean')
files = []
for pattern in patterns:
    matches = sorted(glob.glob(pattern))
    files.extend(matches or [pattern])
extra = os.environ.get('EXTRA_B64', '')
if extra:
    injected = out / 'injected.lean'
    try:
        injected.write_bytes(base64.b64decode(extra, validate=True))
    except ValueError as exc:
        print('Invalid extra_b64:', exc, file=sys.stderr)
    else:
        files.append(str(injected))
for index, filename in enumerate(files, 1):
    fixture_id = Path(filename).stem
    safe_name = ''.join(c if c.isalnum() or c in '-_.' else '_' for c in fixture_id)
    target = out / f'{index:03d}-{safe_name}'
    result = subprocess.run([str(root / 'runner/verify_one.sh'), filename, fixture_id, str(target)])
    print(f'{fixture_id}: exit {result.returncode}', flush=True)
