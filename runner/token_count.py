"""Core1 tools_token_count.py rules, MIT licensed; YinkaiYu/riemann-hypothesis-zero-free-region-lean4."""
import re
from pathlib import Path

LEXER = re.compile(r"[\w']+|[!#$%&*+./:<=>?@^|~\-]+|[^\w\s]", re.U)
BLOCK = re.compile(r"/\-[\s\S]*?\-/")
LINE_COMMENT = re.compile(r"--[^\n]*")
IMPORT = re.compile(r"(?m)^\s*import[^\n]*")


def clean(source):
    return IMPORT.sub('', LINE_COMMENT.sub('', BLOCK.sub(' ', source)))


def report(path):
    raw = Path(path).read_text(encoding='utf-8-sig')
    stripped = clean(raw)
    return {'tokens': len(LEXER.findall(stripped)), 'chars': len(stripped),
            'raw_chars': len(raw), 'lines': raw.count('\n') + 1}
