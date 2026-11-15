from pathlib import Path
import socket, base64, zlib, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_cuda_20261114_v1/control/launch_once_v1.sh')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNq9Vtty2jgYvvdTqNnu3nQcSz67M+6OAROYAKaYtNvZ3dHIOoAbY7s+ZJNOH74ygSY03dlDCzfG6P/1nSSQfnqmJWmuJaReKzVvgMpbpd2Q+hpAx1EoA9q62HDtfXFzR3KNMFIWad5U+K+iutbm8n1ZKb+DZ0Cd3HeCP8GnT4Dfpg1AOjoo7UD+ueMrmv88Yafr/87TsmJVf9dkjVYkT0mGE1qXWLRZtiGbhBwDU4v7r/FiiEnVpCKlXQNtGcE61G2EkIlv0Fe0m2uWVkAtv5N4h3N09Qq/LYuqAf2rQYDfjONxbxLiQfhm3A9j/2J+pTKSUOp6jkqo7alcEKqapuGqxEauzTjxCCEPIL1JEOO30eIyngf9EPej2XB84b80oWe/dPdt0XSOZ1dTvBwtwmAQ+/q+ML2cfLsQzcPZFvqb1fm75SiaDaLZ8u1ivAx775ZhPxqE/hdz0/mkF/Qvw9nAD1arR6P3+gbjhX/0oLVNmdEiF+nqIPJ+0B/JwMdxIIN/ULyczk+jqtmUhzGOgngUh+HAh/vx0RCPrno4Gg4n49ljjYtgFg+jxTRcxE+r3axoGp7AwlpgSuia75l/G1zsYj2RgAP2pdyC0ezLup5kDau0KfJdCN0p84IrWltX26OnSTe8aOXJo9bpKieZvwwXU/ntOs0ylYiGVz6CNUAulE+tKBtN7lJGNJ7f1A9y1XsxHWB516yL3DhHEKhjoMZA7f2bv6lmnVYMl9LHnba1WNMPuBJP3TwpErZJ6zqVDm/QeXkntVf8Q8vr5ofS/k3O/JbTtunId6SdiPd1kT/IUOs10S0buJZrmUI3DaZ7EEJKHQI5d50EGsKkXDc8xxTU05lnMlsw0/EEsz2L267sTAxdIpJWZlulH0nH+EPtyUVtqiLTDhgeeTkY3zuyoeEIJBzHI8hEMEGMWhZFDpEWPDsRUHoyXcvj3Ews3TEsxzC559rIthhl3OsyavNuBx7Fyw778Yrcj+z1O0IGTnVkMQ8SoifQFBBB07BdJEsJga7NdZYQgnQoP1BChEVcjwnoCBcmOnh1/B9vRtqcrs8lCtBf/YKUivrPf93dFZWyknQCnP1c/5GfgbPnFT07habuMoNpwfh5c9so26vNllv5DA2Ks4o='))
assert hashlib.sha256(b).hexdigest() == '60c1963e98cd8250cde90f33bcfa39f7c591f69de39e223daa0303bd56314dd0'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == '60c1963e98cd8250cde90f33bcfa39f7c591f69de39e223daa0303bd56314dd0'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))