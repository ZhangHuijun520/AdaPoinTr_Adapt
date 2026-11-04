"""Local original-byte serializer. Metadata inspection only; no network/process execution."""
import ast
import base64
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).absolute().parent
PARENT = HERE.parent
PINNED_SCOPE_V1 = '1614cd0bf883b8a700a633d3a8fe5f21981f5a3f9c9729bf36ab19b0d89bd7ed'
PINNED_ENTRY = 'aaa92444334ec61d57f593d51f983e79db1aa4d954d15a487b715e911e34dbc9'
PINNED_ACCEPTANCE = '28588c5ea4d5ad14cdb60f1e8fc52f9474629230ef1150c11f61888322a20527'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read_exact(path, sha256, size=None):
    p = Path(path).absolute()
    if any(x.is_symlink() for x in (p, *p.parents)):
        raise ValueError('linked source: ' + str(p))
    before = p.stat()
    raw = p.read_bytes()
    after = p.stat()
    if (before.st_ino, before.st_size, before.st_mtime_ns) != (
            after.st_ino, after.st_size, after.st_mtime_ns):
        raise ValueError('source changed: ' + str(p))
    if digest(raw) != sha256 or size is not None and len(raw) != size:
        raise ValueError('original-byte binding: ' + str(p))
    encoded = base64.b64encode(raw).decode('ascii')
    decoded = base64.b64decode(encoded, validate=True)
    if decoded != raw or digest(decoded) != sha256:
        raise ValueError('Base64 roundtrip: ' + str(p))
    return raw, encoded


def render_in_memory(scope_path, scope_sha256, future_grant_utf8):
    """No launch. A later separately authorized caller must supply the actual new grant."""
    scope_raw, scope_b64 = read_exact(scope_path, scope_sha256)
    scope = json.loads(scope_raw)
    if scope['status'] != 'AWAITING_EXPLICIT_USER_AUTHORIZATION' or scope['execution_authorized'] is not False:
        raise ValueError('pending request required')
    if not isinstance(future_grant_utf8, bytes) or not future_grant_utf8.strip():
        raise ValueError('new explicit grant UTF8 bytes required; old grant must not be reused')
    future_grant_utf8.decode('utf-8', errors='strict')
    q = scope['entry_request']
    a = scope['migration_acceptance']
    if q['sha256'] != PINNED_ENTRY or a['sha256'] != PINNED_ACCEPTANCE:
        raise ValueError('fixed scientific request or migration acceptance changed')
    q_raw, q_b64 = read_exact(q['path'], q['sha256'], q['bytes'])
    a_raw, a_b64 = read_exact(a['path'], a['sha256'], a['bytes'])
    template_binding = scope['local_serialization']['controller_template']
    template_raw, _ = read_exact(template_binding['path'], template_binding['sha256'],
                                 template_binding['bytes'])
    replacements = {
        '__EXECUTION_SCOPE_SHA256__': scope_sha256,
        '__EXECUTION_SCOPE_RAW_BASE64__': scope_b64,
        '__ENTRY_REQUEST_RAW_BASE64__': q_b64,
        '__MIGRATION_ACCEPTANCE_RAW_BASE64__': a_b64,
        '__FUTURE_EXPLICIT_GRANT_UTF8_BASE64__': base64.b64encode(future_grant_utf8).decode('ascii'),
    }
    text = template_raw.decode('ascii')
    for token, value in replacements.items():
        if text.count(token) != 1:
            raise ValueError('exact template placeholder: ' + token)
        text = text.replace(token, value)
    rendered = text.encode('ascii')
    tree = ast.parse(text, feature_version=(3, 8))
    recovered = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in ('SCOPE_RAW', 'Q_RAW', 'ACCEPT_RAW'):
                call = node.value
                if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Attribute):
                    raise ValueError('Base64 assignment AST')
                recovered[name] = base64.b64decode(ast.literal_eval(call.args[0]), validate=True)
    for name, raw in [('SCOPE_RAW', scope_raw), ('Q_RAW', q_raw), ('ACCEPT_RAW', a_raw)]:
        if recovered.get(name) != raw:
            raise ValueError('rendered original bytes differ: ' + name)
    return rendered


def inspect_original_files():
    # Deliberately no controller execution, subprocess, WSL, server or GPU.
    definitions = [
        ('prior_scope', PARENT / 'training_execution_request_v1.json', PINNED_SCOPE_V1, 17659),
        ('entry_request', PARENT / 'training_entry_request_v2.json', PINNED_ENTRY, 5370),
        ('migration_acceptance', PARENT / 'migration_uncertainty_acceptance_v1.json', PINNED_ACCEPTANCE, 2259),
    ]
    values = []
    for kind, path, expected, size in definitions:
        raw, encoded = read_exact(path, expected, size)
        values.append(dict(kind=kind, path=str(path), bytes=len(raw), sha256=digest(raw),
                           Base64_decode_equal=True, Base64_SHA256_equal=True,
                           Base64_ascii_bytes=len(encoded)))
    return dict(status='ORIGINAL_BYTE_BASE64_STATIC_PASS', sources=values,
                production_or_controller_execution=False, server_operations=0)


if __name__ == '__main__':
    if sys.argv[1:] != ['--inspect-originals']:
        raise SystemExit('Only --inspect-originals is supported; no execute option.')
    print(json.dumps(inspect_original_files(), ensure_ascii=True, indent=2))
