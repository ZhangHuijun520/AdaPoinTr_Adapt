from pathlib import Path
import socket, base64, zlib, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Static_D_training_20261115_v1/control/launch_once_v1.sh')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNq9lm1v4kYQx9/7U7jp9d5Ujp/X9km+ymATUABTTO56UqXVPoIvxvat12nop+8SIAnqqTqpCu/YmfHM7z8zGvHzTyYuaxOjbqN1TOoG67V+i7p73QoCjVDd3DRbZn5tHnaoNhFFbVPWUsC/GnFvLtTvldC297QUutH+QKxZNevOJALVJaogJl0LeV9VW7TF6Jjn/yUxi+HvcDmChUSyJJA3FU1hxxi1oBSorKFjOcC2bR8+2Bp7bBsh9eFdmsBPk2IymGYwzT5NhlkR3yzuDIowIWEUGIiAyGAcEcPz3NBAwA4BZShCCL0kGUyTAn7Ol7fFIhlmcJjPR5Ob+INnReBDeArLZws4v5vB1XiZJWkROyfH7Hb6fUe+yOZPqb/rXXxZjfN5ms9Xn5eTVTb4ssqGeZrFz+Jmi+kgGd5m8zRO1utX1gNfOlnGl+u4uW0r0tS8XJ/1fpgMx6rzkyJRE3hBX80WF8aT2/a8seOkGBdZlsbWyT4ewfHdAOaj0XQyfw27TObFKF/OsmXxb+/+q3yWXVLLhkOCyIadEP5Ib46NvjTJGcZKrWk+fx75ZccrStnUx7bsr92vTDP7TjydQFluWdOrC2h05bpGVbzKljP1ui+rykBcMhH7nR4Cz7I63WxaaapNpshk9UP3wm0cqPYJ253cNLV7bVu6MdGNQjcGP3Lc5KYUFLZIyJ35pLUj36DgJ4XpQVdZr8+k/XckU0V2Kuy63SlFgn3rWSffDuZ8Jq85HhnpZalmcGTYM33tmvqFyug2yPGBjsOIOjikNmcIuOoOexxbXhBSwjzqhC7yAwxwEHiY4YAQGnBmeZZL1MvGgAKVEfVqAKL8G+0rvp1atQZSNJV5Vu6VsDP7SV7oOQHHvh3RAHgAuK6jlAQOilwfMJ/Z1EY44g7HwMcWtW3qENfiFgIBtRBn4b5hfb3f2bcXdiz0elYHy/OsqO0A6vnERdh3mGtTN8QcAItT7GFiEx4qBRFg2HEtZEU4ZAS7DqfU4U7guvrHCx6BCvU12VyrdLrz8b2tCRK/++3430drharL9atfuj/rK/3qnSBXF4Vjj6WEpKHsWj5Kbf86QGj/AKNYWT8='))
assert hashlib.sha256(b).hexdigest() == '738e730dd9c721a983c210e69afbda629db0fd80f04801486c8d7e8c6851a43e'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == '738e730dd9c721a983c210e69afbda629db0fd80f04801486c8d7e8c6851a43e'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))