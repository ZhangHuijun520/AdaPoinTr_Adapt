from pathlib import Path
import socket, base64, zlib, hashlib, json
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_dac_r1_20261115_v1/control/runtime_v1.json')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b85decode('c-l?OIc~%-3_#J|r!Z8<fT$rQaV`^(6a~AO&C3)Ca`(VUlj=7Q|9cq6u-WW43D+^GZO^HRO)E_6ao?AlPj3hxr&|4W__lv;vn0x=hQ!icVlEP)#srlLFxE&670J&uN`@^}Ww%@?LQ*J<4k-2SE5|-R*5ym~<#GRaH|wn$U$AANTuRTLtyg4l?O6+4*i%9!EJV!IRag{3l_@z=7=DIdiGDrn'))
assert hashlib.sha256(b).hexdigest() == '7a650ae40ae1f0a392b520e4aa21e91b3eec5fbeb68b620d437251c2a451e804'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == '7a650ae40ae1f0a392b520e4aa21e91b3eec5fbeb68b620d437251c2a451e804'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_MATERIALIZED', name=p.name, sha256='7a650ae40ae1f0a392b520e4aa21e91b3eec5fbeb68b620d437251c2a451e804')))