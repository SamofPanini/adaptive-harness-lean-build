"""Receipt creation and validation, independent of Lean."""
import json
import shlex
from pathlib import Path

REQUIRED = {'fixture_id', 'file_sha256', 'versions', 'steps', 'verdict_raw',
            'axioms', 'sorry_hits', 'new_axiom_decls', 'statement_sha256',
            'statement_text', 'tokens', 'peak_rss_kb', 'disk_used_bytes',
            'runner', 'started_at', 'finished_at', 'comparator'}
VERDICTS = {0: 'COMPILED_CLEAN', 10: 'ENV_ERROR', 20: 'COMPILE_ERROR',
            21: 'TIMEOUT', 30: 'AXIOM_EXTRA', 31: 'SORRY_FOUND',
            11: 'COMPARATOR_ERROR', 40: 'COMPARATOR_REJECTED'}


def versions():
    values = {}
    for line in (Path(__file__).parent / 'versions.env').read_text().splitlines():
        if line and not line.startswith('#'):
            key, value = line.split('=', 1)
            values[key] = shlex.split(value)[0]
    return values


def validate(data):
    missing = REQUIRED - data.keys()
    if missing: raise ValueError('missing receipt fields: ' + ', '.join(sorted(missing)))
    comp = data['comparator']
    if not isinstance(comp, dict) or not {'status', 'rc', 'seconds', 'peak_rss_kb', 'log_tail'} <= comp.keys():
        raise ValueError('invalid comparator')
    if comp['status'] not in {'ACCEPTED', 'REJECTED', 'TOOL_ERROR', 'TIMEOUT', 'SKIPPED'}:
        raise ValueError('invalid comparator status')
    for name, step in data['steps'].items():
        if not {'rc', 'seconds'} <= step.keys(): raise ValueError('invalid step: ' + name)
    if data['verdict_raw'] not in VERDICTS.values(): raise ValueError('invalid verdict')
    return data


def write(path, data):
    Path(path).write_text(json.dumps(validate(data), ensure_ascii=False, indent=2) + '\n')
