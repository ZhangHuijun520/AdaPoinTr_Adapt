"""Download only the bounded inventory. Server-read-only; no retry or execution."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys

D = Path(__file__).resolve().parent
BASE = ['wsl.exe', '-d', 'Ubuntu-20.04', '--exec']
CLIENT = '/home/zhj/.local/bin/hpc5000'
ROOTS = ['/home/jovyan/adapointr_work/PoinTr/logs/cranial_bcsp_fullmamba/LQI_foldC_seed0_train_20261111_v1',
         '/home/jovyan/adapointr_work/PoinTr/third_party/bcsp_lqi_foldC_training_20261111_v1']


def main():
    inventory = json.loads((D/'inventory_before_stdout.bin').read_bytes())
    assert not inventory['tmux_present'] and not inventory['worker_PID_exists']
    assert len(inventory['rows']) == 33 and inventory['bytes'] <= 2*1024**3
    folder = D/'downloaded'; folder.mkdir(exist_ok=False)
    wsl = subprocess.run(BASE+['wslpath', '-a', str(folder)], capture_output=True, timeout=15)
    assert wsl.returncode == 0
    wsl_root = wsl.stdout.decode('utf-8').strip()
    assert wsl_root.startswith('/mnt/e/') and '\n' not in wsl_root
    receipts = []
    metadata_rows = [r for r in inventory['rows'] if not (r['role'] == 0 and r['name'] == 'ckpt-last.pth')]
    assert len(metadata_rows) == 32 and sum(r['bytes'] for r in metadata_rows) <= 64*1024**2
    for i, row in enumerate(metadata_rows):
        name = PurePosixPath(row['name'])
        assert not name.is_absolute() and '..' not in name.parts
        assert name.suffix not in ('.npz', '.npy', '.pth', '.pt', '.ckpt', '.nrrd', '.stl')
        role = ['output', 'installed'][row['role']]
        local = folder/role/row['name']; local.parent.mkdir(parents=True, exist_ok=True)
        assert not local.exists()
        remote = str(PurePosixPath(ROOTS[row['role']])/name)
        target = str(PurePosixPath(wsl_root)/role/name)
        r = subprocess.run(BASE+[CLIENT, 'get', remote, target], capture_output=True, timeout=30)
        for key, blob in [('stdout', r.stdout), ('stderr', r.stderr)]:
            with (D/('get_'+str(i)+'_'+key+'.bin')).open('xb') as f:
                f.write(blob)
        assert r.returncode == 0, 'download failed, no retry: '+remote
        blob = local.read_bytes()
        assert len(blob) == row['bytes'] and hashlib.sha256(blob).hexdigest() == row['sha256'], remote
        receipts.append(dict(remote=remote, local=str(local), bytes=len(blob), sha256=row['sha256']))
        print(json.dumps(dict(downloaded=i+1, total=32, name=row['name'])), flush=True)
    with (D/'collection_receipt_v1.json').open('x', encoding='ascii') as f:
        json.dump(dict(status='ALL32_NONCHECKPOINT_ARTIFACTS_DOWNLOADED_AND_HASH_MATCH', files=receipts,
                       server_writes=0, CUDA_calls=0, retries=0), f, indent=2)


if __name__ == '__main__':
    try:
        main()
    except BaseException as exc:
        with (D/'collection_failure_v1.json').open('x', encoding='ascii') as f:
            json.dump(dict(status='FAILED_STOP_NO_RETRY', error=repr(exc)), f)
        raise
