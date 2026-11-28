"""Pure local authorization byte materialization; performs no installation or dispatch."""
import hashlib
import json
import re


def materialize(request_raw, authorization_text, *, execution_authorized):
    if execution_authorized is not True:
        raise ValueError('Separate execution authorization required')
    if not isinstance(authorization_text, str) or not authorization_text.strip():
        raise ValueError('Explicit authorization text required')
    request_sha = hashlib.sha256(request_raw).hexdigest()
    # Reject an instruction bound to another request rather than silently relabeling it.
    mentioned = re.findall(r'(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])', authorization_text)
    if any(value != request_sha for value in mentioned):
        raise ValueError('Authorization text binds a different request')
    if request_sha not in authorization_text:
        authorization_text = authorization_text.rstrip() + '\nrequest SHA256=' + request_sha
    authorization = dict(schema='bcsp-development-authorization-v1',request_sha256=request_sha,
                         explicit_user_authorization=True,user_authorization_text=authorization_text)
    encode = lambda value: json.dumps(value,separators=(',',':'),ensure_ascii=True).encode('ascii')
    auth_raw = encode(authorization)
    runtime_raw = encode(dict(schema='bcsp-development-runtime-v1',request_sha256=request_sha,
                              authorization_sha256=hashlib.sha256(auth_raw).hexdigest()))
    return auth_raw, runtime_raw
