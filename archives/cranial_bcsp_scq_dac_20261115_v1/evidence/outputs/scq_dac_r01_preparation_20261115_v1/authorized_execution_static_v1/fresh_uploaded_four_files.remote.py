from pathlib import Path
import hashlib, json, socket
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0'

def h(p):
    a = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda : f.read(4194304), b''):
            a.update(b)
    return a.hexdigest()
for r in [{'path': 'scq_dac_r1_frozen20_transport_20261115_v1.tar.gz', 'bytes': 906620311, 'sha256': '350717ccaa584b93faa49b808355a762a94563f842f9e5f3352bf9a7973e0e01'}, {'path': 'scq_dac_r1_frozen20_transport_20261115_v1.tar.gz.sha256', 'bytes': 116, 'sha256': '95f38be8c7d7c905a18fa01962590d40f1748f711c7e2441909f9c8a4c426393'}, {'path': 'scq_dac_r1_frozen20_transport_20261115_v1.tar.gz.bytes', 'bytes': 11, 'sha256': '03edefedf07e76d0d649d875924c389ea4c518e4275bfbaabd852d7bfd3d9d19'}, {'path': 'scq_dac_r1_frozen20_transport_20261115_v1.tar.gz.contents.sha256', 'bytes': 3453, 'sha256': 'f16e5c10713a91fa93479f85d93103fcb45acfb7248b06200c722865e0140bd3'}]:
    p = Path('/home/jovyan') / Path(r['path']).name
    assert p.is_file() and (not any((x.is_symlink() for x in (p, *p.parents)))) and (p.stat().st_size == r['bytes']) and (h(p) == r['sha256'])
print(json.dumps(dict(status='FRESH_FOUR_UPLOAD_HASHES_PASS', files=4)))