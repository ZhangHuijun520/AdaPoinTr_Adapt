from pathlib import Path
import socket, base64, zlib, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_D_training_20261114_v1/control/launch_once_v1.sh')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNq9VmFvo0YQ/c6voOn1vlSEZYEFTuIqbHBsxTauce56UqXVsLvYXDBwC6Rxf31x7CS2eqpOquJv7Mzw5r03y4iff9LTvNRTaDZKI1pVE53SbaG5V5HjKIyr+qbaCv1r9bCDUgcOdZWXraR/VfJeX/TPK6ls73kuVa3+gVq9qNaNziSUORQ0ZU1Ns64otrBN4Yjz/0D0ZPg7XY5oIkVGs6rgIW2E4Ii2EvKSYoSJYRgWfTAU8VhXslWHd2FAP02SyWAa0TD6NBlGiX+zuNM4pIy5nqMBI54mMmCaZZmuBsRwCRfgAcAryGAaJPRzvLxNFsEwosN4Pprc+B8s5JEP7nNZPFvQ+d2MrsbLKAgTHz8nZrfT7yfiRTR/gv5udvFlNY7nYTxffV5OVtHgyyoaxmHkv4ibLaaDYHgbzUM/WK9Pogd+4WTpX8pvfVsXrCqzfH3m/DAYjnvfJ0nQ+/9KfDVbXJRcu63PTR0HyTiJotBHz/HxiI7vBjQejaaT+SnVZTBPRvFyFi2Tf2f3b8Wz6HJKNhllwDbimcAf4c3R5MvyOCOx6q9nPH8Z9iUHK/O2Ko+W7Dfcr0LRu0Y+rb0234qq67ee1uTrEgp/FS1n/ek+LwoNslZI325Ul1gINape1a3e32AOuigfmlfW2oHTHrDetZuqNK8NpGoTVUtUbfAjC63d5JLTGmS705+UNuwbldlBX3hQlZfrM2H/VSf6Bru+6Lre9Wqk+NaJpn0rIqezOOXwKFjX5r33x/57Pl+bqnxlpDUbwDZRXdcFbqYG2IbHMUnBQ06KiEEsUxCEATJhYZ4hgRAizOGIIMKxhYUHNkOI94jQ9cbL/G/Yd3wrpf3wW1kV+lmzE1ln8Wdx3HK5Y6Q2AMOeQ7jLbTPFxDQdhs3MBQc7DkuxzQEQcczUNEwGpmf0kpFhcm9vV1fub+pbyzq2OZ3TIfIyJ9vIDAdc18DCZA4TmSkczDLbIZlJbGYxlrmO5dpZhgXnfY2wOCfYMU1LIM9RP17ssy+gK9nmugdT8cf3hiKZ/+634x+OUsu+a6Ze/dL8WV6pV+8ku7ogNfGYt5RVXFy3j62yPx0oKP8AVDRLAg=='))
assert hashlib.sha256(b).hexdigest() == '0901af12e7c11e92e5c71a6aac71ac7b1be148ab4b3a243b078e652fdcf9d695'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == '0901af12e7c11e92e5c71a6aac71ac7b1be148ab4b3a243b078e652fdcf9d695'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))