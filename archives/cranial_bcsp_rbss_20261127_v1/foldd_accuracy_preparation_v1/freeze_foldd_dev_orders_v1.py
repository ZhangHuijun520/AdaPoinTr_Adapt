"""Precompute Fold D development permutations from frozen residuals and OASG anchors."""
import io
import json
from collections import Counter
from pathlib import Path
import sys
import tarfile
import time

import numpy as np
import scipy
from threadpoolctl import threadpool_limits

STAGE = Path(__file__).resolve().parent
ROOT = STAGE.parent
sys.path[:0] = [str(ROOT / d) for d in ('p0b_v1', 'p0c_v1', 'p1_v1')]
import run_p0b_v1 as pilot
from rbss_geometry_v1 import fit_plane, native_order, plan_orders
from rbss_order_v1 import content_key
from run_p0c_v1 import check_serialization, triples


def main():
    start = time.perf_counter()
    output = STAGE / 'FoldD_dev105_orders_freeze_v1.json'
    need, sha, bound = pilot.need, pilot.digest, pilot.bound
    need(not output.exists(), 'fresh development output')
    amendments = list(ROOT.glob('*精度验证协议修订案_2026-11-27_v1.md'))
    need(len(amendments) == 1 and sha(amendments[0].read_bytes()) ==
         'd28a0f2e37c8aef50e0e6c975589bba18ae4d9bacc7da30b310eb60a631d7308', 'approved amendment')
    p0b = json.loads(bound(pilot.SELECTION, '6232f8a751f60360c0bb0cca9e509702dba005be275cb98182c62c13a44a94a8'))
    need(pilot.local_source_hashes() == p0b['sources'] and (np.__version__, scipy.__version__) == (p0b['numpy'], p0b['scipy']), 'exact geometry code/runtime')
    geo = Path(fit_plane.__code__.co_filename)
    geometry_sha = sha(geo.read_bytes())
    need(geometry_sha == 'bb33cccefa73d27056c1a66d57f606fac0547eba738c4ddf76d1654084236daf', 'P1 geometry')
    need(sha(Path(content_key.__code__.co_filename).read_bytes()) == '14a101c4db689eb95b2cadc6601b3de634f6ad8a46094f44d96417382164b39f', 'P1 content key source')
    p0c = json.loads(bound(ROOT / 'p0c_v1/P0c_scope_v1.json', '20785a17ecc9fec2da90b84025f738f4c1b1a080ea1563dc68a1ddc239d083c0'))
    need(sha(Path(check_serialization.__code__.co_filename).read_bytes()) == p0c['p0c_runner_sha256'], 'P0c serialization review source')
    fold = json.loads(bound(pilot.PAYLOAD / 'fold_binding.json', pilot.FOLD))['folds']['D']
    manifest = {r['case_id']: r for r in map(json.loads, bound(pilot.PAYLOAD / 'manifest_8192.jsonl', pilot.MANIFEST).splitlines())}
    dev = fold['dev_case_ids']
    need(len(dev) == len(set(dev)) == 105 and not set(dev) & set(fold['train_case_ids']), 'exact development IDs')
    arc_root = Path('E:/ResearchBackups/AdaPoinTr/BCSP_OASG/2026-11-24_foldD_native_eval_v2')
    p4 = ROOT.parent / 'bcsp_oasg_20261124_v1/p4_ba_d_v2'
    audit_sha = 'e21d072568380335f88fc610242766a7a06be6a82dce02be7e4df42b00e75d1d'
    audit = json.loads(bound(p4 / 'P4_v2_formal_post_prediction_freeze_receipt_v1.json', audit_sha))
    need(audit['stable_rehash'] and audit['exact_case_order'] and audit['case_pairs'] == 105
         and audit['diagnostics']['A_exact_Q_equals_S_plus_delta_and_token_index'] == 105, 'historical anchor diagnostics')
    anchor_archive_sha = 'd2757690cec30cb48c62efdd2f186a968c66d330581895d08bee55c9c89de3fd'
    downloads = {Path(r['path']).name: r for r in audit['downloads']}
    files = {name: bound(arc_root / name, r['sha256']) for name, r in downloads.items()}
    arc_name = 'development_predictions_v1.tar.gz'
    need(sha(files[arc_name]) == anchor_archive_sha, 'exact anchor archive')
    members = {n: h for h, n in (line.split(maxsplit=1) for line in files[arc_name + '.contents.sha256'].decode('ascii').splitlines())}
    records = []
    with tarfile.open(fileobj=io.BytesIO(files[arc_name]), mode='r:gz') as t, threadpool_limits(limits=1):
        names = t.getnames()
        [mn] = [n for n in names if n.endswith('inference_manifest.jsonl')]
        data = t.extractfile(mn).read()
        need(sha(data) == members[mn], 'manifest hash')
        aa = {r['case_id']: r for r in map(json.loads, data.splitlines()) if r['variant'] == 'A'}
        need(list(aa) == dev and {n for n in names if n.startswith('predictions/A_D__')} ==
             {'predictions/A_D__' + cid + '.npz' for cid in dev}, 'historical A identities and order')
        for index, cid in enumerate(dev, start=1):
            rec, inp = aa[cid], manifest[cid]
            frame = inp['normalization']
            need(rec['checkpoint_sha256'] == pilot.CHECKPOINT and rec['normalization'] == frame
                 and rec['input_sha256'] == inp['sha256'], 'coordinate contract ' + cid)
            m = 'predictions/A_D__' + cid + '.npz'
            raw = t.extractfile(m).read()
            need(sha(raw) == members[m] == rec['prediction']['sha256'], 'anchor member ' + cid)
            with np.load(io.BytesIO(raw), allow_pickle=False) as z:
                s, ids = z['S'], z['token_index']
            with np.load(io.BytesIO(bound(pilot.POINTS / inp['point_path'], inp['sha256'])), allow_pickle=False) as z:
                x = z['partial']
            need(x.shape == (8192, 3) and s.shape == (256, 3) and x.dtype == s.dtype == np.float32
                 and np.isfinite(x).all() and np.isfinite(s).all() and np.array_equal(ids, np.arange(256))
                 and not (triples(s.tobytes()) - triples(x.tobytes())), 'D-only anchor identity ' + cid)
            center, scale = np.asarray(frame['center'], dtype=np.float64), frame['scale']
            need(center.shape == (3,) and np.isfinite(center).all() and np.isfinite(scale) and scale > 0, 'physical frame ' + cid)
            s_mm = s.astype(np.float64) * scale + center
            o = native_order(s)
            plane = fit_plane(x.astype(np.float64) * scale + center)
            seq = plan_orders(s, s_mm, plane)
            check_serialization(plane, seq, o, s_mm)
            records.append(dict(case_id=cid, source_id=inp['source_id'], type=cid.split('__',2)[2],
                                point_npz_sha256=inp['sha256'], ordered_input_sha256=sha(x.tobytes()),
                                anchors_sha256=sha(s.tobytes()), anchor_member_sha256=members[m],
                                native_order_sha256=sha(o.astype('<i8').tobytes()), normalization=frame,
                                permutation_content_key=content_key(x, frame, s, o, geometry_sha, 'RBSS-v2'),
                                plane=plane, serialization=seq))
            if index % 35 == 0:
                print('DEVELOPMENT', index, 105, flush=True)
    active = [r for r in records if r['serialization']['joint_active']]
    kinds = Counter(x['type'] for x in active)
    srcs = Counter(x['source_id'] for x in active)
    gates = dict(active_at_least_74=len(active) >= 74,
                 each_type_at_least_11=all(kinds[k] >= 11 for k in pilot.TYPES),
                 sources_with_at_least_three_at_least_15=sum(v >= 3 for v in srcs.values()) >= 15,
                 offline_order_integrity=True)
    need(len({r['permutation_content_key'] for r in records}) == 105, 'distinct content keys')
    summary = dict(cases=105, active=len(active), fallback=105-len(active), by_type=dict(kinds),
                   sources_with_at_least_three=sum(v >= 3 for v in srcs.values()), offline_G6=gates,
                   live_G6='PENDING_ACTUAL_PAIRED_PREDICTIONS', prefix_calls=0, model_calls=0,
                   seconds=time.perf_counter()-start)
    pilot.write_once(output, dict(schema='bcsp-rbss-foldD-development-orders-v1', summary=summary,
                                  historic_archive_sha256=anchor_archive_sha, historic_audit_sha256=audit_sha,
                                  fold_binding_sha256=pilot.FOLD, point_manifest_sha256=pilot.MANIFEST,
                                  geometry_sha256=geometry_sha, runner_sha256=sha(Path(__file__).read_bytes()), records=records))
    print(json.dumps(dict(summary=summary, result_sha256=sha(output.read_bytes()))), flush=True)


if __name__ == '__main__':
    main()
