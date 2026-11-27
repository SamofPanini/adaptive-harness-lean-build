#!/usr/bin/env python3
"""Prepare a pinned Mathlib checkout and record setup timings."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from receipt import versions

out = Path(os.environ['OUTPUT_DIR']).resolve()
out.mkdir(parents=True, exist_ok=True)
mathlib = Path(os.environ['MATHLIB']).resolve()
v = versions()
revision = os.environ.get('MATHLIB_REV_OVERRIDE') or v['MATHLIB_REV']
steps = {name: {'rc': None, 'seconds': None} for name in ('toolchain', 'mathlib', 'cache')}
os.environ['PATH'] = str(Path.home() / '.elan/bin') + os.pathsep + os.environ.get('PATH', '')


def run(name, command, cwd=None, timeout=1200):
    start = time.monotonic()
    try:
        with (out / ('setup_' + name + '.log')).open('w') as log:
            result = subprocess.run(command, cwd=cwd, stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
        rc = result.returncode
    except subprocess.TimeoutExpired:
        rc = 124
    except OSError as exc:
        (out / ('setup_' + name + '.log')).write_text(str(exc) + '\n')
        rc = 127
    steps[name] = {'rc': rc, 'seconds': round(time.monotonic()-start, 3)}
    return rc == 0


status = 'INFRA_FAIL'
try:
    # Install only the requested toolchain; no Mathlib build command is issued.
    if (run('toolchain', ['bash', '-c', 'set -o pipefail; curl -sSf https://elan.lean-lang.org/elan-init.sh | sh -s -- -y --default-toolchain none && "$HOME/.elan/bin/elan" toolchain install "$1"', 'bash', v['LEAN_TOOLCHAIN']])
        and run('mathlib', ['bash', '-c', 'set -e; git init "$1"; git -C "$1" remote add origin "$2"; git -C "$1" fetch --depth 1 origin "$3"; git -C "$1" checkout --detach FETCH_HEAD', 'bash', str(mathlib), v['MATHLIB_REPO'], revision])
        and run('cache', [str(Path.home() / '.elan/bin/lake'), 'exe', 'cache', 'get'], cwd=mathlib)):
        status = 'OK'
finally:
    receipt = {'setup_status': status, 'mathlib_rev': revision, 'steps': steps,
               'disk_free_bytes': shutil.disk_usage(out).free}
    (out / 'setup_receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print('setup_status=' + status)
