from pathlib import Path
import socket, os, hashlib, tarfile, json, subprocess, time
assert socket.gethostname() == 'shu-common-25721452-notebook-qx2k0r-0' and os.getuid() == 1000
start = time.monotonic()
total = 0
p = Path('/home/jovyan/bcsp_scq_rf_sixmodel_native_pending_20261115_v1.tar.gz')
assert not any((x.is_symlink() for x in (p, *p.parents))) and p.stat().st_size < 1048576 and (hashlib.sha256(p.read_bytes()).hexdigest() == '552d439ddd85293d66c6b9c632fbb4110a68dc6d60b7452eb705e991946640ca')
with tarfile.open(p) as t:
    idx = json.loads(t.extractfile('payload/RF_sixmodel_input_index_v1.json').read())
rows = list({r['input']['path']: r for r in idx['inputs']}.values())
assert len(rows) == 210 and len(idx['inputs']) == 630
for root in ['/home/jovyan/adapointr_work/PoinTr/data/bcsp_geov1_foldc_8192_seed0_v1/points', '/home/jovyan/adapointr_work/PoinTr/data/bcsp_geov1_foldd_8192_seed0_v1/points']:
    p = Path(root)
    assert p.is_dir() and (not any((x.is_symlink() for x in (p, *p.parents))))

def state():
    return dict(targets=[dict(path=x, exists=Path(x).exists(), symlink=Path(x).is_symlink()) for x in ['/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_sixmodel_prediction_20261115_v1', '/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/SCQ_RF_sixmodel_native_development_20261115_v1', '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_sixmodel_prediction_20261115_v1/control/attempt_claim_v1.json', '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_sixmodel_prediction_20261115_v1/control/native_prediction_authorization_v1.json', '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_sixmodel_prediction_20261115_v1/control/native_prediction_runtime_v1.json', '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_scq_rf_sixmodel_prediction_20261115_v1/control/native_prediction_launch_once_v1.sh']], tmux_live=subprocess.run(['tmux', 'has-session', '-t', 'bcsp_scq_rf_six_native_20261115_v1'], capture_output=True).returncode == 0)
before = state()
out = []
for row in rows:
    expected = row['input']
    name = Path(expected['path']).name
    assert name == row['case_id'] + '_8192.npz'
    candidates = []
    for root in ['/home/jovyan/adapointr_work/PoinTr/data/bcsp_geov1_foldc_8192_seed0_v1/points', '/home/jovyan/adapointr_work/PoinTr/data/bcsp_geov1_foldd_8192_seed0_v1/points']:
        p = Path(root) / name
        checks = dict(exists=p.exists(), no_links=not any((x.is_symlink() for x in (p, *p.parents))))
        r = dict(path=str(p))
        r.update(checks=checks)
        if checks['exists'] and checks['no_links']:
            checks['regular_file'] = p.is_file()
            if checks['regular_file']:
                st = p.stat()
                r['bytes'] = st.st_size
                checks['size_matches'] = st.st_size == expected['bytes']
                checks['bounded_size'] = st.st_size <= 2097152
                if checks['bounded_size']:
                    assert time.monotonic() - start < 50 and total + st.st_size <= 268435456
                    h = hashlib.sha256()
                    with p.open('rb') as f:
                        for b in iter(lambda : f.read(1048576), b''):
                            h.update(b)
                            total += len(b)
                    end = p.stat()
                    assert (st.st_size, st.st_mtime_ns, st.st_ctime_ns) == (end.st_size, end.st_mtime_ns, end.st_ctime_ns)
                    r['sha256'] = h.hexdigest()
                    checks['hash_matches'] = r['sha256'] == expected['sha256']
        r['valid_match'] = all((checks.get(k, False) for k in ['exists', 'no_links', 'regular_file', 'size_matches', 'bounded_size', 'hash_matches']))
        candidates.append(r)
    original = next((c for c in candidates if c['path'] == expected['path']))
    out.append(dict(fold=row['fold'], case_id=row['case_id'], expected=expected, original_valid=original['valid_match'], candidates=candidates))
after = state()
assert before == after
print(json.dumps(dict(status='BOUNDED_INPUT_PATH_OBSERVATION_COMPLETE', hostname=socket.gethostname(), uid=os.getuid(), before=before, after=after, rows=out, hashed_bytes=total, seconds=time.monotonic() - start, server_writes=0, array_reads=0, new_forward=0)))