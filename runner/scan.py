"""Scan Lean code while masking nested comments and string literals."""
import re


def mask(source):
    out = list(source)
    i, depth, string = 0, 0, False
    while i < len(source):
        if depth:
            if source.startswith('/-', i):
                out[i:i+2] = '  '; depth += 1; i += 2
            elif source.startswith('-/', i):
                out[i:i+2] = '  '; depth -= 1; i += 2
            else:
                if source[i] != '\n': out[i] = ' '
                i += 1
        elif string:
            if source[i] == '\\' and i + 1 < len(source):
                out[i] = ' '
                if source[i+1] != '\n': out[i+1] = ' '
                i += 2
            elif source[i] == '"':
                out[i] = ' '; string = False; i += 1
            else:
                if source[i] != '\n': out[i] = ' '
                i += 1
        elif source.startswith('/-', i):
            out[i:i+2] = '  '; depth = 1; i += 2
        elif source.startswith('--', i):
            end = source.find('\n', i)
            if end < 0: end = len(source)
            out[i:end] = ' ' * (end-i); i = end
        elif source[i] == '"':
            out[i] = ' '; string = True; i += 1
        else:
            i += 1
    return ''.join(out)


def scan(source):
    code = mask(source)
    hits = [{'word': m.group(), 'line': code.count('\n', 0, m.start()) + 1}
            for m in re.finditer(r"(?<![\w']) (?:sorry|admit) (?![\w'])", code, re.X)]
    decls = [{'name': m.group(1), 'line': code.count('\n', 0, m.start()) + 1}
             for m in re.finditer(r"(?<![\w'])axiom\s+([^\s:({]+)", code)]
    return hits, decls
