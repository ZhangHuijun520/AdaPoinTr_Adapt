from pathlib import Path
import socket, base64, hashlib, json, zlib
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_memory_20261114_v1/control/authorization_v1.json')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNqlUL1Kw1AU3vsUpbOBJL23adzcXJx8gJDcHEnAWpvcSFUERfujbTq1gg0ViyIOJQURGiX4NLlJOuUVbOqiOLodzvn+zndaKBZLNjGgppY286nBWXtcDWp165hTHWrULfNEpWb9gDsSShs52oKGAzZVbEMVcSVnYQFABiRqRJSJXOZ5UZMEUkVI1rAMuoAQLqugVXQsEV0VkVjFEvAIEx2XKzLC37rQPNw3iUkVxwZL+eW9MqGWA2vY36tCoUnzHMnwJe4ukqmf+k9s8RoFN1H4kIV95o6S3iwedOPJZb4MzuPJlPn9ePS2u721eoLN39nHMBlfRYGbPrcT75b51+ljKwoGbDhf4XPKbMrci+izx/z75V1rZ13RstNZeu0s9H6qZeH4340Uzgpfo3mtLA=='))
assert hashlib.sha256(b).hexdigest() == '235c1a571a16d8d1fe756397a5b4f901b4e57b5ff45e24be72d20fee1ef556c9'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == '235c1a571a16d8d1fe756397a5b4f901b4e57b5ff45e24be72d20fee1ef556c9'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))