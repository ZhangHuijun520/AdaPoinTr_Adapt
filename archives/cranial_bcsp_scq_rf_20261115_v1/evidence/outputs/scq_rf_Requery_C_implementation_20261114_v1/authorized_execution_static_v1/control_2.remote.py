from pathlib import Path
import socket, base64, zlib, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Requery_C_training_20261114_v1/control/launch_once_v1.sh')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNq9lm1vm0gQx9/zKbi0d29OhGcWKtETxjhGsY0PnD5IJ62WfbBpMNAFcnE/fZfYTuy7Sq1U1W8QzAwzv//MauDVb2peVGqO2o3U0k5WaC/1W9TeyxoAEiayuqm3VP1UP+xQpSKCmrqoOg7/rfm9uhT3Ky5t70nBZaX5gVi1rNetijmqClTCHLcNZH1ZbtE2R4c8P5dEzcK/YTqBKf3cU76DrC5JCFtKiQY7jooKGprh6LpuwQddoo9NzTs5vBsH8F2cxaNZBMfRuziMMv9meacQlGPsekBB2PEUyhBWLMt0FeTorkMo8hBCL0lGsyCD75P0NlsGYQTDZDGJb/w3luY5b9xjWDJfwsXdHK6maRSMM984Oua3s287kmW0eEr9Te/y42qaLMbJYvU+jVfR6OMqCpNx5D+Lmy9noyC8jRZjP1ivT6x7vnGc+hdsubptSlxXrFifNT8MwqlofZwFYgQv7Kv58tJ83bY5b+00yKZZFI197WifTuD0bgSTyWQWL05p02CRTZJ0HqXZ/73DW8k8uqiYDYMY4Q09MnwY3xxafXGUM46VOKrJ4nnqF54wL7q6OjRm2Hl/UkntW/60CLtiS+te7EGlLdYVKv1VlM7F031RlgpiHeW+3cquY2laK6t106niNBOk0uqhfQFX9lhDwmbXberKvNY1WYllJZOV0Y+suG5TcAIbxLud+iS2xZ8hZ88Sw72wolqfaftOKBVldiLuutkJTXwIaLtfiPOfuZySPFLcd4WYw4FioPrU1tULl9JukGE7sgEos8Wi1bE9XLBhOdTFlm17wHN1ohmm6dg6YTnCDDiG7pgAuQjkpgOQZ3lAZES9GAIvvqCh4i/UK85Cx+tSPat3ouzMftQn2D3NpMADhuaaGhJfGI16yCCuhg2cWzZwXAu5mJGcGtgUBgY0HZuWp1u2buOhY301HNwLKDtUOp3W3nJUkwtSM/dcywEGYdiiNPeow+zcIJpJACOmxZhtmrapiykCw2COxhglBsiB7TJPfnvJXVCivsKba5FPNt7+oUsc+6//OvwISQ0XhZl89Xv7T3UlX73m+OqydPSx6CCuCb3uHjtpeNpTSF8BhSxeNA=='))
assert hashlib.sha256(b).hexdigest() == 'f2fb1523525129e8678267117f5184ea4945c37f4c00aaf25a00eacc874218b4'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == 'f2fb1523525129e8678267117f5184ea4945c37f4c00aaf25a00eacc874218b4'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))