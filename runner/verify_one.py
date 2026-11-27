#!/usr/bin/env python3
"""Run a single verification and always record the observed result."""
import datetime
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

from receipt import VERDICTS, versions, write
from scan import scan
from token_count import report as token_report


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def disk_size(path):
    if not path.is_dir(): return None
    return sum(p.stat().st_size for p in path.rglob('*') if p.is_file() and not p.is_symlink())


def memory_total():
    try:
        for line in Path('/proc/meminfo').read_text().splitlines():
            if line.startswith('MemTotal:'): return int(line.split()[1])
    except OSError: pass
    return None


def run(args, cwd, logfile, timeout=None):
    start = time.monotonic()
    try:
        with logfile.open('w') as log:
            proc = subprocess.run(args, cwd=cwd, stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
        rc = proc.returncode
    except subprocess.TimeoutExpired:
        rc = 124
    except OSError as exc:
        logfile.write_text(str(exc) + '\n'); rc = 127
    return {'rc': rc, 'seconds': round(time.monotonic() - start, 3)}


def main():
    source, fixture_id, out = Path(sys.argv[1]).resolve(), sys.argv[2], Path(sys.argv[3]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    v = versions()
    if os.environ.get('MATHLIB_REV_OVERRIDE'): v['MATHLIB_REV'] = os.environ['MATHLIB_REV_OVERRIDE']
    mathlib = Path(os.environ.get('MATHLIB', '/nonexistent')).resolve()
    started = now()
    data = dict(fixture_id=fixture_id, file_sha256=None, versions=v, steps={}, verdict_raw='ENV_ERROR',
                axioms=[], sorry_hits=[], new_axiom_decls=[], statement_sha256=None, statement_text=None,
                tokens=None, peak_rss_kb=None, disk_used_bytes=None,
                runner={'uname': ' '.join(os.uname()), 'nproc': os.cpu_count(), 'memory_total_kb': memory_total()},
                started_at=started, finished_at=None)
    rc = 10
    try:
        start = time.monotonic()
        env_ok = (source.is_file() and shutil.which('lean') and shutil.which('lake') and
                  (mathlib / 'lakefile.lean').is_file() and (mathlib / '.lake/build/lib/lean').is_dir() and
                  shutil.which('timeout') and Path('/usr/bin/time').is_file() and
                  os.environ.get('SETUP_STATUS', 'OK') == 'OK')
        data['steps']['environment'] = {'rc': 0 if env_ok else 10, 'seconds': round(time.monotonic()-start, 3)}
        if source.is_file():
            raw = source.read_bytes()
            data['file_sha256'] = digest(raw)
            text = raw.decode('utf-8-sig')
            start = time.monotonic()
            data['sorry_hits'], data['new_axiom_decls'] = scan(text)
            data['steps']['scan'] = {'rc': 31 if data['sorry_hits'] else 0, 'seconds': round(time.monotonic()-start, 3)}
            start = time.monotonic(); data['tokens'] = token_report(source)
            data['steps']['tokens'] = {'rc': 0, 'seconds': round(time.monotonic()-start, 3)}
        if not env_ok:
            print('ENV_ERROR: Lean, Lake, Mathlib cache, source, or required tools unavailable')
            return rc
        data['disk_used_bytes'] = disk_size(mathlib / '.lake')
        work = out / 'work'; (work / 'build').mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, work / 'Solution.lean')
        # lake env supplies Mathlib search paths; prepend the local compiled module.
        command = ['lake', 'env', 'bash', '-c', 'export LEAN_PATH="$1/build:$LEAN_PATH"; shift; exec "$@"', 'bash', str(work)]
        compile_args = command + ['/usr/bin/time', '-v', '-o', str(out / 'time.log'), 'timeout', v['COMPILE_TIMEOUT_SEC'],
                                  'lean', '-j2', '--tstack=400000', '--root=' + str(work), '-o', str(work / 'build/Solution.olean'), str(work / 'Solution.lean')]
        step = run(compile_args, mathlib, out / 'compile.log', int(v['COMPILE_TIMEOUT_SEC']) + 30)
        data['steps']['compile'] = step
        timefile = out / 'time.log'
        if timefile.exists():
            match = re.search(r'Maximum resident set size \(kbytes\):\s*(\d+)', timefile.read_text())
            if match: data['peak_rss_kb'] = int(match.group(1))
        log = (out / 'compile.log').read_text(errors='replace')
        if "declaration uses 'sorry'" in log:
            data['sorry_hits'].append({'word': 'sorry', 'source': 'compile.log'})
            data['steps']['scan']['rc'] = 31
        if step['rc']:
            rc = 21 if step['rc'] in (124, 137) else 20
            return rc
        audit = work / 'Audit.lean'
        audit.write_text('import Solution\n#print axioms ' + v['TARGET_DECL'] + '\n')
        step = run(command + ['lean', '-j2', '--tstack=400000', '--root=' + str(work), str(audit)], mathlib, out / 'axioms.log', 120)
        data['steps']['axioms'] = step
        axout = (out / 'axioms.log').read_text(errors='replace')
        match = re.search(r'depends on axioms:\s*\[(.*?)\]', axout, re.S)
        if step['rc'] or (not match and 'does not depend on any axioms' not in axout):
            rc = 10; return rc
        data['axioms'] = [x.strip() for x in match.group(1).split(',') if x.strip()] if match else []
        audit.write_text('import Solution\nset_option pp.all true in\n#check @' + v['TARGET_DECL'] + '\n')
        step = run(command + ['lean', '-j2', '--tstack=400000', '--root=' + str(work), str(audit)], mathlib, out / 'statement.log', 120)
        data['steps']['statement'] = step
        statement = (out / 'statement.log').read_text(errors='replace')
        if step['rc'] or not statement.strip(): rc = 10; return rc
        data['statement_text'] = statement
        data['statement_sha256'] = digest(' '.join(statement.split()).encode())
        if data['sorry_hits']: rc = 31
        elif set(data['axioms']) - set(v['PERMITTED_AXIOMS'].split()): rc = 30
        else: rc = 0
        return rc
    except (OSError, UnicodeError, ValueError) as exc:
        print('ENV_ERROR:', exc, file=sys.stderr); rc = 10; return rc
    finally:
        data['verdict_raw'] = VERDICTS[rc]
        data['finished_at'] = now()
        write(out / 'receipt.json', data)
        print('verdict_raw=' + data['verdict_raw'])


if __name__ == '__main__': sys.exit(main())
