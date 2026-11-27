#!/usr/bin/env python3
"""Prepare a pinned Mathlib checkout and record setup timings."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from receipt import versions
from comparator import create_judge
import hashlib

out = Path(os.environ['OUTPUT_DIR']).resolve()
out.mkdir(parents=True, exist_ok=True)
mathlib = Path(os.environ['MATHLIB']).resolve()
v = versions()
revision = os.environ.get('MATHLIB_REV_OVERRIDE') or v['MATHLIB_REV']
steps = {name: {'rc': None, 'seconds': None} for name in ('toolchain', 'mathlib', 'cache', 'landrun', 'nanoda', 'lean4export', 'comparator', 'challenge')}
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
comparator_status = 'SKIPPED'
tools = {}
challenge_text = None
challenge_hash = None
try:
    # Install only the requested toolchain; no Mathlib build command is issued.
    if (run('toolchain', ['bash', '-c', 'set -o pipefail; curl -sSf https://elan.lean-lang.org/elan-init.sh | sh -s -- -y --default-toolchain none && "$HOME/.elan/bin/elan" toolchain install "$1"', 'bash', v['LEAN_TOOLCHAIN']])
        and run('mathlib', ['bash', '-c', 'set -e; git init "$1"; git -C "$1" remote add origin "$2"; git -C "$1" fetch --depth 1 origin "$3"; git -C "$1" checkout --detach FETCH_HEAD', 'bash', str(mathlib), v['MATHLIB_REPO'], revision])
        and run('cache', [str(Path.home() / '.elan/bin/lake'), 'exe', 'cache', 'get'], cwd=mathlib)):
        status = 'OK'
        comparator_status = 'INFRA_FAIL'
        base = out / 'tools'
        base.mkdir(exist_ok=True)
        checkout = 'set -e; git init "$1"; git -C "$1" remote add origin "$2"; git -C "$1" fetch --depth 1 origin "$3"; git -C "$1" checkout --detach FETCH_HEAD'
        builds = [
            ('landrun', ['go', 'build', '-o', 'landrun', 'cmd/landrun/main.go'], 'landrun'),
            ('nanoda', ['cargo', 'build', '--release'], 'target/release/nanoda_bin'),
            ('lean4export', ['lake', 'build'], '.lake/build/bin/lean4export'),
            ('comparator', ['lake', 'build'], '.lake/build/bin/comparator'),
        ]
        for name, build, binary in builds:
            directory = base / name
            shell = checkout + ('; printf "%s\\n" "$4" > "$1/lean-toolchain"' if name in ('lean4export', 'comparator') else '')
            # Checkout and build are recorded as one step.
            cmd = ['bash', '-c', shell + '; cd "$1"; shift 4; exec "$@"', 'bash', str(directory), v[name.upper() + '_REPO'], v[name.upper() + '_REV'], v['LEAN_TOOLCHAIN'], *build]
            if run(name, cmd, timeout=3600):
                tools[name] = str((directory / binary).resolve())
        judge = out / 'challenge-template'
        start = time.monotonic()
        try:
            create_judge(judge, mathlib, v['LEAN_TOOLCHAIN'])
            audit = judge / 'Audit.lean'
            audit.write_text('import Challenge\nset_option pp.all true in\n#check @' + v['TARGET_DECL'] + '\n')
            build = judge / 'build'
            build.mkdir()
            # Use the existing Mathlib environment directly: never invoke a Mathlib build.
            command = ['lake', 'env', 'bash', '-c', 'export LEAN_PATH="$1:$LEAN_PATH"; shift; exec "$@"', 'bash', str(build)]
            with (out / 'setup_challenge.log').open('w') as log:
                result = subprocess.run(command + ['lean', '-j2', '--tstack=400000', '--root=' + str(judge), '-o', str(build / 'Challenge.olean'), str(judge / 'Challenge.lean')], cwd=mathlib, stdout=log, stderr=subprocess.STDOUT, timeout=1200)
                rc = result.returncode
                if rc == 0:
                    result = subprocess.run(command + ['lean', '-j2', '--tstack=400000', '--root=' + str(judge), str(audit)], cwd=mathlib, capture_output=True, text=True, timeout=120)
                    rc = result.returncode
                    log.write(result.stdout + result.stderr)
                    if rc == 0 and result.stdout.strip():
                        challenge_text = result.stdout
                        challenge_hash = hashlib.sha256(' '.join(challenge_text.split()).encode()).hexdigest()
                    else:
                        rc = rc or 1
        except subprocess.TimeoutExpired:
            rc = 124
        except OSError as exc:
            (out / 'setup_challenge.log').write_text(str(exc) + '\n'); rc = 127
        steps['challenge'] = {'rc': rc, 'seconds': round(time.monotonic()-start, 3)}
        if all(steps[name]['rc'] == 0 for name in ('landrun', 'nanoda', 'lean4export', 'comparator', 'challenge')):
            comparator_status = 'OK'
finally:
    receipt = {'setup_status': status, 'mathlib_rev': revision, 'steps': steps,
               'disk_free_bytes': shutil.disk_usage(out).free, 'comparator_status': comparator_status,
               'tools': tools, 'challenge_statement_sha256': challenge_hash,
               'challenge_statement_text': challenge_text}
    (out / 'setup_receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print('setup_status=' + status)
