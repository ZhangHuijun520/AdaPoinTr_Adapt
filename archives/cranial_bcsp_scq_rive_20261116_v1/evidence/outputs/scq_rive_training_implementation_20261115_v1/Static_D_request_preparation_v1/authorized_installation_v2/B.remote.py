import pathlib, json, hashlib, tarfile, io, socket, os, subprocess
P = pathlib.Path
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0' and os.getuid() == 1000
p = P('/home/jovyan/bcsp_rive_Static_D_pending_20261115_v1.tar.gz')
b = p.read_bytes()
h = hashlib.sha256(b).hexdigest()
assert len(b) == 8031 and h == '1f349b82560ace2e04af6982fbdeb6dcd489f11618eae1769521308e5941e39b'
with tarfile.open(fileobj=io.BytesIO(b), mode='r:gz') as t:
    ms = t.getmembers()
    assert len(ms) == len({m.name for m in ms}) == 2 and sum((m.size for m in ms)) < 65536
    data = {}
    for x in ms:
        n = pathlib.PurePosixPath(x.name)
        assert x.isfile() and (not n.is_absolute()) and ('..' not in n.parts)
        data[x.name] = t.extractfile(x).read()
        assert len(data[x.name]) == x.size
contents = ''.join((hashlib.sha256(v).hexdigest() + '  ' + n + '\n' for (n, v) in sorted(data.items())))
for (suf, text) in [('.bytes', '8031\n'), ('.sha256', h + '  ' + p.name + '\n'), ('.contents.sha256', contents)]:
    x = P(str(p) + suf)
    assert x.is_file() and (not any((v.is_symlink() for v in (x, *x.parents)))) and (x.read_bytes() == text.encode())
m = json.loads(data['installation_mapping_v1.json'])
I = m['identity']
args = ['/usr/bin/nvidia-smi', '--id=' + I['gpu_uuid'], '--query-gpu=uuid,name,driver_version,memory.total', '--format=csv,noheader,nounits']
g = [x.strip() for x in subprocess.check_output(args, text=True, timeout=10).strip().split(',')]
assert g == [I['gpu_uuid'], I['gpu_name'], I['driver_version'], str(I['nvidia_smi_memory_total_MiB'])]
print(json.dumps(dict(status='UPLOAD_AND_GPU_PASS', gpu=g, members=2, server_writes=0)))
