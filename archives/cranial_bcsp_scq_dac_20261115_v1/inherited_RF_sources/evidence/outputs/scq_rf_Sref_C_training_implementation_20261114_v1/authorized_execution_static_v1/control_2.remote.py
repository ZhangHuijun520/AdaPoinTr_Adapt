from pathlib import Path
import socket, base64, zlib, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_Sref_C_training_20261114_v1/control/launch_once_v1.sh')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNq9ltuOm0gQhu95CnaSzU3EcDSHSGSFMR5bYxsvMDlIK7Wqm26bDAbSwGScp097bGdsbbSKtBrfQXVR9f1/NQ2v/lBxUakY2rXU0k5WaC/1G2jvZc1xJJLL6rreUPVL/bCFSoUcmrqoOo6+1fxeXYrrjEub+7zgstL8Rq5a1qtWJRyqAkqESdsg1pflBjYYDnX+XxE1Df9GyRilnDLE6jIPUUtprqGOQ1EhQzNsXdct9KBL9LGpeSeHd6MAfZim0+EsQqPowzSMUv9meafkgAlxPUcBYnsKZUAUyzJdBWzdtXMKHgA8FxnOghR9jJPbdBmEEQrjxXh647+zNM9+5x7T4vkSLe7mKJskUTBKfeO4ML+d/XohXkaLp9K/XF1+zibxYhQvso/JNIuGn7MojEeR/1PcfDkbBuFttBj5wWp1Et3zjaaJfym/1U1TkrpixerM+TAIJ8L3aRoI/5/Bs/nyonDdpjk3dRKkkzSKRr52jE/GaHI3RPF4PJsuTlGTYJGO42QeJem/V3dPxfPockrWDBEga3oE+DS6OZh8WY4ziExsz3jxc9iXHCwvuro6WLI74d5SSe1b/nTsdcWG1r049ZS2WFVQ+lmUzMXdfVGWCrCOcn/Qyq5taVorq3XTqWIH56DS6qF9plb2TLuCzbZb15V5rWuyMpWVVFaGv3OgdeuC56gB3m3VJ6Ut+Yo42+sL96qKanUm7L/yqGiwFUnXzVao4fRrT9vupUBOZ3HK8EhJ3xXC+0P/Hc+Xtq6eiZR2DcbAlu3cNommaTm1BkwzCKUOdUzdBUxzoEzD2LOx6VHTgAHVgNrM0nDOMDOI7WBDFxWhF8bz4jvsOr6UUjH8jteletbsRNZZ/CjOw7nnEEyZBUauYQFvWgyb2BFaLctzLBg4FiHi0+LZzGWgu9RhBqaiLdFNvBPH+2q3U19a1qHN6Zz2kaMU3XMNUwDqtqUTz2WOruGBq1nUsAByC2ys4xwPGLUMputgiAGJkYrxYYcRx8by+4u99iX0FVlfi2Ky8f6NLnHiv/7r8IcjNVx0ZfLVn+0/1ZV89ZqTqwui0ceiQ6TO6XX32Em7uz2C9AMPJU2q'))
assert hashlib.sha256(b).hexdigest() == '4a688e674e27223cf6566544bac3184ec3a9a25e2c89f3d6899b58c1b2eb02f0'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == '4a688e674e27223cf6566544bac3184ec3a9a25e2c89f3d6899b58c1b2eb02f0'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))