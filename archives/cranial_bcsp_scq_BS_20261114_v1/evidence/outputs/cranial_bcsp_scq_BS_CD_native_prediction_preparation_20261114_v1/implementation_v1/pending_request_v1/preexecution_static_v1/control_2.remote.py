from pathlib import Path
import socket, base64, hashlib, json, zlib
assert socket.gethostname() == 'shu-common-25721452-notebook-t6ibfm-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_BS_CD_prediction_20261114_v1/control/native_prediction_launch_once_v1.sh')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNq9Vltv2zYYfdevYLOuL4MikpIoqYA6yJIcG7Etz3LaFdsgUCRlq9GtunjJ0B8/2bETuymwSxG/Ud/1nPNRJH94pcRpocS0WUuNaIEsOqnLaXMLoGFIjANlXeZC+VRu7mmhUE6rMi3aOvqzrG+Veb9e1tJv4BWQJw+R4A/w5QsQd2kLEEYnrn2Rf474qs1/Ttjj+r95Slaumu9KVlhNi5RmUcyaKkq6LMtpHtOXqKmE7i/RIIxcLypom25ExMVGZGWVi6KNMMQEIaRFG/RV8/yWpzWQKyDL34ngUEo+FxNJ3FVl3QL3xnOi9+NwPJj4kee/H7t+aF/Nb2RKLUGSJJYTHscyMlUiI6Zi2cCahlXEVQNpT0UGEyeMPgSL63DuuH7kBrPh+Mp+q0GLvDUPYcF0Hs1uptFytPAdL7TxwTG9nnzbEcz92a70N73zj8tRMPOC2fLDYrz0Bx+Xvht4vv1IbjqfDBz32p95trNaHVkf8HnjhX0muZW8ylhZJOnqRHjXcUe97OPQ6eV/wr2czs+Jrc2rU0lHTjgKfd+z4cE+Gkajm0EUDIeT8ewY6cKZhcNgMfUX4XPvNiuY+mcjsk4iRtlaHPr/6l3tJT4rjBMMy35rBrPHSZ9xqnXalsVekO2t9JOQlK6pd1dVm+ai7PqbSm7SVUEze+kvpv3XbZplMk1aUdt6AwwMYQOUsmqVfvNyqohi0zxhlh8QbetV9+26LNRLBIE8BnII5MG/OcnadVrzqKJ1e6/seDbs855dVQuesjbtKRyzeoxKyq7OSy6ygw77hD7osrrvqdTicyea9mVgPJvCUZy4E6zbrfYQtpA+NWXxBEpu1hTrBBgEIgtRERND01VVqBriBtQhj3UTqpagMeGcGRpG1DDUOFFJDHVhIsIFhZhpfUXa9crX6V902/FlyPazb+syU55TPWl+RPPEfiBLY0aJlaiQ4xirlBE9saiKDcOEOo0tqCIDmlzXOTQxMoWmEoJVJjA1MCVCN7fydcV2556b5r7t8RwfLAdq3ECQ01hQljDOEaEwMS3NslRmJUhYuoUR02lCdIwpg4RrPOnHSHVuWUQzIQHvznUqZLQr2PqyrwXwuzdIqpn9+uf9o1Wq6r5pAi5+bH4vLsDF65pdnA/Z9lUVsf6PvmzvWmn3xtohkP4G56ro0Q=='))
assert hashlib.sha256(b).hexdigest() == 'ca470768504dc370693c9285cf723e70f5759ed7963a84c1a68a62b216d40f01'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == 'ca470768504dc370693c9285cf723e70f5759ed7963a84c1a68a62b216d40f01'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))