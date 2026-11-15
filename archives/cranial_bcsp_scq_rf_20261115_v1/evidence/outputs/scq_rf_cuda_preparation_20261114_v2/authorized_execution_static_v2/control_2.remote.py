from pathlib import Path
import socket, base64, zlib, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v2/control/launch_once_v2.sh')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNq9VtuSmzYYvucplG3SmwwL4iTIDMlgjNeetY0L3qSZtKMRkrDJYiActruZPHyF13twNp22SewbjPVL3+mXLf3yTEmyQklIs5Ya3gKZd1K3Ic0lUBGSKAPKutxw5WN5dUMKhTBSlVnR1vivsr5UFuJ9WUsfwDMgT29ngj/Bly+AX2ctgBrcK+1A/n3GVzT/e8FO1/euU/Jy1fzQYoXWpMhIjhPaVDjt8nxDNgk5BKYS+7/haIRJ3WZpRvsJtGMEa6pmQQgNfKV9Rbu5ZFkN5OoHiXc4B1cv8euqrFvgXww9/HYSTwbTAA+DtxM/iN2zxYXMSEKp7SCZUMuReUqobBi6LRML2hbjxCGEPIAMpl6M34XRebzw/AD74Xw0OXNfGapjvbLvpoWzBZ5fzPByHAXeMHbvRczOp98uhItgvoX+ZnXxfjkO58NwvnwXTZbB4P0y8MNh4MJ73MV04PnnwXzoeqvVo9FbfcNJ5B48aGVT5bQs0my1F7nv+WMR+CT2RPAPipezxXFUtZtqP8axF4/jIBi66t34eITHFwMcjkbTyfyxxsibx6MwmgVR/LTarwpnwREsrFNMCV3zO+bfh2e7WI8kYI99KbZgOL/v61F6WGdtWexC6E+Zl1xSuqbeHj1ttuFlJ04euclWBcndZRDNxLfLLM9lkra8dqHaAGir4qmUVauIXcqIwour5kGufCumB6xu2nVZ6KdQBfIEyDGQB//lb6pdZzXDlfBxo2wtNvQTrtOnbp4UCdtkTZMJh1faaXUjtNf8U8eb9qfS/kPO/JrTru3Jd6S9iI9NWTzIkJs10UwLqA7jlmqYqcYpRZZqmraqO1Sjmok0gzsGJ1xFdmJqKTIMwlOLa6aJDBOZHCY0FYikE9nW2WfSM/5Ue6KpbV3myh7DIy974/eOdM1wHESg5ei2ypOEWQRZ1E6YjWxk6Q6EBCVcU1EKTQQN4ZVCRhjVE1Nl3Okz6op+Bx7Eyw77cUduR+70M4YspOtmynWRdMpSVeSvQQSRk9gUGY7oA1LFJ+dIc0iCEqJqFNqpYVnUFBv89eF/vDnpCro+FShAe/0rlGrqPn+zuytKVS3oUnDyovmjOAEnz2t6cgxN/WUG05Lx0/a6lbZXmy239Df5orJn'))
assert hashlib.sha256(b).hexdigest() == '17feb78e33b38e132d5c0286939fa6fe2cbd4ff84b8e08354875d64981808bc3'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == '17feb78e33b38e132d5c0286939fa6fe2cbd4ff84b8e08354875d64981808bc3'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))