from pathlib import Path
import socket, base64, hashlib, json, zlib
assert socket.gethostname() == 'shu-common-25721452-notebook-zbpgzu-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_memory_20261114_v1/control/launch_once_v1.sh')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNq9VtuSmzYYvucplE3amw6LBIhDZkgH23jtWdu4xpvDpB2NEMImyylCbNedPHyx187ayc70kMR3oF/6Tr9Aev5Mi7NSi2mzVhougcpbpS1ocwugbSssAdq6Krj2obrb0FKjCa2rrJSC/FmJW23ePS+F8h48A+rkYSb4A3z6BPh9JgHS0UlpD/LPM76g+c8L9rr+7zotr1bNNy3WmKBlRnMSs6YmaZvnBS1i+iMwtaj/G1kMieQloUy23YSCF5XYEB3qFkLIJHfoC+LiNskEUGugqt/IfoBSz+FC4fd1JSTo3wx88nocjXuTgAyC1+N+EHlX8xs1oTFjjmurlFmuylPKVNM0HJVayLESTl1K6SNIb+JH5E24uI7mfj8g/XA2HF95L03oWi+dw7RwOiezmylZjhaBP4g8/VCYXk+eLoTzYLaDfrI6f7cchbNBOFu+WYyXQe/dMuiHg8D7bG46n/T8/nUwG3j+anU0+qBvMF54Z4haK+qcVWWarU5C7/v9URf5OPK76B81L6fzc+mSRX0a5ciPRlEQDDx4GB8NyeimR8LhcDKeHatc+LNoGC6mwSL6urpdFU6Ds5hYp4RRtuYH7reDq320Z5Nwwr/stmI4+9zdM3VSZLIq90FsT55fuKK1jdgdRzIreNV2p5HaZKuS5t4yWEy7t9ssz1WaSi483ADkQNgAraql1m3WhGq8vGse9aoParZ49Uauq9K4RBCoY6BGQO39mz+WXGciITUVcqPtPDbsIxHpU3aeKDNay1bwrnpZbzrxgn9seSO/M/FR2Psqv+eslVkX7p5xq+BDU5WPGtRmTXVsAYw4d7mpx0x3mWtAqMc2Yo5pujF2eYJMExuUx1aCbZZQ3dQdbHNoYpZgw3JN3CHStotWZH/RLeN39tZ1VYoq1044jtycjB886QZmiGIbUWQlToJSbmPLcG2KYzN1IYpNju0Yp6mJuW7G3NYTHaacI55ibDF3m1JbbnfgD3KzRz/uysPIwUGXum1DyDlLDYclXX947EJodPKRo0OXwZimNkZYNww9gUi3HWY6KE1MJ8VmCsGrc3zAOW1Ltr7scID+6mekCOa9+HV/h1Rq0RGm4OKn5vfyAly8EOziPKq2lxzCqoRfynup7K48O3blb8wavvY='))
assert hashlib.sha256(b).hexdigest() == 'f323bb51b05695d8bf17e6e25f4743e61a450536ba90c215d322b59c677e9d6c'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == 'f323bb51b05695d8bf17e6e25f4743e61a450536ba90c215d322b59c677e9d6c'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))