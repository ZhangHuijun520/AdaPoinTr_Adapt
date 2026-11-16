import pathlib, json, hashlib, tarfile, io, socket, os, subprocess
P = pathlib.Path
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0' and os.getuid() == 1000
p = P('/home/jovyan/bcsp_rive_Requery_D_pending_20261115_v1.tar.gz')
b = p.read_bytes()
h = hashlib.sha256(b).hexdigest()
assert len(b) == 12264 and h == 'a3fef516e809b92d5835be2377cad840e77c06e482ef2a0519cd0b7c8ba3e2d6'
with tarfile.open(fileobj=io.BytesIO(b), mode='r:gz') as t:
    ms = t.getmembers()
    assert len(ms) == len({m.name for m in ms}) == 3 and sum((m.size for m in ms)) < 65536
    data = {}
    for x in ms:
        n = pathlib.PurePosixPath(x.name)
        assert x.isfile() and (not n.is_absolute()) and ('..' not in n.parts)
        data[x.name] = t.extractfile(x).read()
        assert len(data[x.name]) == x.size
contents = ''.join((hashlib.sha256(v).hexdigest() + '  ' + n + '\n' for (n, v) in sorted(data.items())))
for (suf, text) in [('.bytes', '12264\n'), ('.sha256', h + '  ' + p.name + '\n'), ('.contents.sha256', contents)]:
    x = P(str(p) + suf)
    assert x.is_file() and (not any((v.is_symlink() for v in (x, *x.parents)))) and (x.read_bytes() == text.encode())
m = json.loads(data['installation_mapping_v1.json'])
I = m['identity']
args = ['/usr/bin/nvidia-smi', '--id=' + I['gpu_uuid'], '--query-gpu=uuid,name,driver_version,memory.total', '--format=csv,noheader,nounits']
g = [x.strip() for x in subprocess.check_output(args, text=True, timeout=10).strip().split(',')]
assert g == [I['gpu_uuid'], I['gpu_name'], I['driver_version'], str(I['nvidia_smi_memory_total_MiB'])]
print(json.dumps(dict(status='UPLOAD_AND_GPU_PASS', gpu=g, members=3, server_writes=0)))
