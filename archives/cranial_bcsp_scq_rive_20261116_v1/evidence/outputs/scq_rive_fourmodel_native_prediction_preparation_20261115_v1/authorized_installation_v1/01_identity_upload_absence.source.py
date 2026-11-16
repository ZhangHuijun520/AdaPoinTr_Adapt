import pathlib, json, hashlib, tarfile, io, os, socket
P = pathlib.Path
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0' and os.getuid() == 1000
p = P('/home/jovyan/bcsp_rive_fourmodel_native_pending_20261115_v1.tar.gz')
assert not any((x.is_symlink() for x in (p, *p.parents)))
b = p.read_bytes()
assert len(b) == 83164 and hashlib.sha256(b).hexdigest() == 'ae7f8633365a8cd483590f1c6dc5087e6afa0887554db31028f6e2d1ef5036ef'
with tarfile.open(fileobj=io.BytesIO(b), mode='r:gz') as t:
    mb = t.extractfile('installation_mapping_v1.json').read()
assert hashlib.sha256(mb).hexdigest() == 'c67690dc37f1b3d77a0822ac3069cb508cdca1b7c4bac536702a9aadbe383dd5'
m = json.loads(mb)
import subprocess
with tarfile.open(fileobj=io.BytesIO(b), mode='r:gz') as t:
    ms = t.getmembers()
    assert len(ms) == len({x.name for x in ms}) == 16 and sum((x.size for x in ms)) <= 1048576
    data = {}
    for x in ms:
        n = pathlib.PurePosixPath(x.name)
        assert x.isfile() and (not n.is_absolute()) and ('..' not in n.parts)
        data[x.name] = t.extractfile(x).read()
        assert len(data[x.name]) == x.size
ct = ''.join((hashlib.sha256(v).hexdigest() + '  ' + n + '\n' for (n, v) in sorted(data.items())))
for (suf, v) in [('.bytes', str(len(b)) + '\n'), ('.sha256', hashlib.sha256(b).hexdigest() + '  ' + p.name + '\n'), ('.contents.sha256', ct)]:
    x = P(str(p) + suf)
    assert x.is_file() and (not any((y.is_symlink() for y in (x, *x.parents)))) and (x.read_bytes() == v.encode()), str(x)
I = m['identity']
g = [x.strip() for x in subprocess.check_output(['/usr/bin/nvidia-smi', '--id=' + I['gpu_uuid'], '--query-gpu=uuid,name,driver_version,memory.total', '--format=csv,noheader,nounits'], text=True, timeout=10).strip().split(',')]
assert g == [I['gpu_uuid'], I['gpu_name'], I['driver_version'], str(I['nvidia_smi_memory_total_MiB'])]
root = P(m['install_root'])
assert m['new_install_root'] is True and (not os.path.lexists(root)) and (root.parent == P(m['parent_must_already_exist'])) and root.parent.is_dir()
assert not any((x.is_symlink() for x in (root, *root.parents))) and len(m['files']) == 15
for r in m['files']:
    x = P(r['target'])
    assert x.parent == root and (not os.path.lexists(x)) and (r['overwrite'] is False)
for x in m['must_remain_absent']:
    assert not os.path.lexists(x), x
print(json.dumps(dict(status='IDENTITY_UPLOAD_AND_ABSENCE_PASS', gpu=g, tar_members=16, targets_absent=15, new_root_absent=True, server_writes=0)))
