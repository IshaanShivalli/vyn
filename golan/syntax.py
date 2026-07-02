"""Golan syntax support for PL.

This module exports Go-style syntax helpers and parser functions used by
`scripts` and by the `.go` source loader.
"""

import fnmatch
import glob as _glob
import os
import re

FUNCTION_HEADER_RE = re.compile(
    r'^function\s*(?P<fname>[A-Za-z_]\w*)?\s*\(\s*(?P<params>.*?)\s*\)\s*(?:returns\s*\(\s*(?P<returns>.*?)\s*\)\s*)?perform\s*$',
    re.IGNORECASE,
)

GO_FUNC_HEADER_RE = re.compile(
    r'^func\s+(?P<fname>[A-Za-z_]\w*)\s*\(\s*(?P<params>.*?)\s*\)\s*(?:returns\s*\(\s*(?P<returns>.*?)\s*\))?\s*\{$'
)


def _parse_param(p):
    p = p.strip()
    if '=' in p:
        name, default = p.split('=', 1)
        return name.strip(), default.strip()
    return p, None


def _strip_param_types(params):
    cleaned = []
    for part in params.split(','):
        part = part.strip()
        if not part:
            continue
        if ' ' in part:
            cleaned.append(part.split()[0])
        else:
            cleaned.append(part)
    return ', '.join(cleaned)


def parse_function_header(line):
    m = FUNCTION_HEADER_RE.match(line.strip())
    if not m:
        return None
    fname = m.group('fname')
    raw = m.group('params')
    returns_raw = m.group('returns')
    params = [_parse_param(p) for p in raw.split(',') if p.strip()]
    returns = [r.strip() for r in returns_raw.split(',')] if returns_raw else []
    return fname, params, returns


def parse_go_function_header(line):
    m = GO_FUNC_HEADER_RE.match(line.strip())
    if not m:
        return None
    fname = m.group('fname')
    params_raw = m.group('params')
    returns_raw = m.group('returns')
    params = _strip_param_types(params_raw)
    params = [p.strip() for p in params.split(',') if p.strip()] if params else []
    returns = [r.strip() for r in returns_raw.split(',')] if returns_raw else []
    return fname, params, returns


def match(pattern, name):
    return fnmatch.fnmatch(name, pattern)


def filepath_match(pattern, path):
    return fnmatch.fnmatch(path, pattern)


def glob(pattern):
    return list(_glob.glob(pattern))


def recursive_glob(pattern, root='.'):
    results = []
    root = os.path.abspath(root)
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            rel = os.path.relpath(os.path.join(dirpath, filename), root)
            if fnmatch.fnmatch(rel, pattern):
                results.append(rel)
    return results


def regex_match(pattern, text):
    return bool(re.match(pattern, text))


def regex_search(pattern, text):
    return bool(re.search(pattern, text))


def regex_findall(pattern, text):
    return re.findall(pattern, text)


def register_syntax(variables):
    variables.update({
        'match': match,
        'filepathMatch': filepath_match,
        'glob': glob,
        'recursiveGlob': recursive_glob,
        'regexMatch': regex_match,
        'regexSearch': regex_search,
        'regexFindAll': regex_findall,
    })


def preprocess_go_source(lines):
    result = []
    in_import_block = False
    for line in lines:
        no_comment = line.split('//', 1)[0]
        stripped = no_comment.strip()
        if not stripped:
            continue
        if in_import_block:
            if stripped == ')':
                in_import_block = False
                continue
            if stripped.startswith('"') and stripped.endswith('"'):
                result.append(f'import {stripped[1:-1]}')
            continue
        if stripped.startswith('package '):
            continue
        if stripped.startswith('import '):
            if stripped == 'import (':
                in_import_block = True
                continue
            target = stripped[7:].strip()
            if target.startswith('"') and target.endswith('"'):
                target = target[1:-1]
            result.append(f'import {target}')
            continue
        if stripped.startswith('func '):
            header = stripped[5:].strip()
            if header.endswith('{'):
                header = header[:-1].strip()
            returns = ''
            if ' returns ' in header:
                header, returns = header.split(' returns ', 1)
                returns = returns.strip()
                if returns.startswith('(') and returns.endswith(')'):
                    returns = returns[1:-1].strip()
            if '(' in header and ')' in header:
                name = header[:header.index('(')].strip()
                params = header[header.index('(')+1:header.rindex(')')].strip()
                params = _strip_param_types(params)
                if returns:
                    result.append(f'function {name}({params}) returns ({returns}) perform')
                else:
                    result.append(f'function {name}({params}) perform')
                continue
        if stripped == '}':
            result.append('endFunc')
            continue
        result.append(stripped)
    return result
