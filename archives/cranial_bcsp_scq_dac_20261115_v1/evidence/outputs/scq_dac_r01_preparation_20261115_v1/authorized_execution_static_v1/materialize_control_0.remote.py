from pathlib import Path
import socket, base64, zlib, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_dac_r1_20261115_v1/control/authorization_v1.json')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b85decode('c-p0q&rZTX5XSF31?kx)-AzkdZ{EE70L{`ap$Sslwu%}P)F=WiUbHb14vj$*!ygZX)WF-&F6G24xRn#}=w&9EZ|3)Xnaf;0&)IqzA0uu*&lPpM#v4fI3E+|Ilr3UjAjh<-{3+n}vR#5tTx>g<T}DtUWH$h+sDzPFkdXis0RlymfhsD3qyj~haMlb7>Y@RaqKfr`EC~P>fvk!ch)CITalKYCb<@#Y8xw8Eo0&Mo#lLHRRn5V5C(98>oj7XH(ID}kSDhh!>8`>t?LN@{Z9E?^H5q&Kd3tnsz=CfU9&P!_<7D0R*PkBkhw*&2Y+T2YpT6I(dO<R7rEho1_l&ka($GtuCJdhOhanVL*}_T|IYY$QEIMK~G_Y<NnDAD$a?W7u-i-F9H26v<Z5oW0jhi@Xvmi8RZh5<jUjO~c+*R%ee?rRl'))
assert hashlib.sha256(b).hexdigest() == 'ccfd8c934d6a5677f6e6cf8491ebf6b7139e224b54755995fba9ab41bb952e45'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == 'ccfd8c934d6a5677f6e6cf8491ebf6b7139e224b54755995fba9ab41bb952e45'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_MATERIALIZED', name=p.name, sha256='ccfd8c934d6a5677f6e6cf8491ebf6b7139e224b54755995fba9ab41bb952e45')))