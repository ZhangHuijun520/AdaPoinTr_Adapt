
"""Extend the frozen EJTC G-label pilot to the remaining Fold D training cases."""
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from collections import Counter
import importlib.util
from pathlib import Path
import sys
import time

import replay_g_pilot15_v1 as pilot

HERE = Path(__file__).resolve().parent
PILOT = pilot.OUT
OUT = HERE / "p0b_full315_v1"
PILOT_SCOPE = "7cf2053635419113bf7c246fd4923afb7c19b393984efe2338f2e253d35c2eab"
PILOT_RESULT = "dfb3a5800c1220fcb49d2283e0b12fb6fa2a09d91bbcac43aae36b9317fe18cd"
WORKERS = 3
sampler = None


def initialize():
    global sampler
    pilot.OUT = OUT
    spec = importlib.util.spec_from_file_location("ejtc_frozen_sampler", pilot.SOURCE)
    sampler = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sampler)


def work(row, state):
    np = sampler.np
    rng = np.random.Generator(np.random.PCG64())
    rng.bit_generator.state = state
    sampler.CASE_START = time.monotonic()
    record = pilot.replay(sampler, row, rng)
    return record, sampler.PEAK_RSS


def readback(directory, case, frozen_row, record_sha, np):
    from hashlib import sha256
    record_path = directory / f"{case}.json"
    record = pilot.read_json(record_path)
    sidecar = directory / f"{case}_labels.npz"
    assert pilot.sha(record_path) == record_sha
    assert record["case_id"] == case and record["source_id"] == frozen_row["source_id"]
    assert record["split"] == "D/train" and record["raw"] == frozen_row["raw"]
    assert record["source_point_sha256"] == frozen_row["sha256"]
    assert record["target_ordered_fp32_sha256"] == frozen_row["target_array_sha256"]
    assert record["ordered_target_byte_match"] and record["sidecar"] == sidecar.name
    assert record["sidecar_sha256"] == pilot.sha(sidecar)
    scope = directory / "pilot_scope.json"
    assert record["rng_manifest_sha256"] == pilot.sha(scope)
    assert record["sampler_sha256"] == pilot.EXPECTED[pilot.SOURCE]
    with np.load(sidecar, allow_pickle=False) as z:
        lab, ix, keys, fov = [z[k] for k in ("labels_G","face_index","face_key","is_fov")]
        assert lab.shape == ix.shape == fov.shape == (8192,) and keys.shape == (8192,5)
        assert lab.dtype == np.uint8 and np.isin(lab,(0,1)).all() and fov.dtype == np.bool_
        assert not np.any(lab[fov]) and np.all(ix >= 0)
        for v, k in ((lab,"labels_sha256"),(ix,"face_index_sha256"),(keys,"face_key_sha256")):
            assert sha256(v.tobytes()).hexdigest() == record[k]
        assert int(lab.sum()) == record["n_J"] and 8192-int(lab.sum()) == record["n_E"]
        assert min(record["n_J"],record["n_E"]) >= 32
        assert len(record["spot_checks"]) == 16
        checks = Counter(p["is_j"] for p in record["spot_checks"])
        assert checks == {False:8, True:8}
        for checked in record["spot_checks"]:
            i = checked["row"]
            assert 0 <= i < 8192 and keys[i].tolist() == checked["face_key"]
            assert bool(lab[i]) == checked["is_j"] == checked["opposite_d"]
            assert bool(fov[i]) != checked["opposite_inside"]
    return record


def main():
    selected = pilot.matched_rows()
    assert pilot.sha(PILOT/"pilot_scope.json") == PILOT_SCOPE
    assert pilot.sha(PILOT/"pilot_result.json") == PILOT_RESULT
    previous = pilot.read_json(PILOT/"pilot_result.json")
    assert previous["status"] == "P0B_PILOT15_PASS"
    prior_hashes = {r["case_id"]:r["record_sha256"] for r in previous["records"]}
    pilot_ids = [r["case_id"] for r in selected]
    assert list(prior_hashes) == pilot_ids and len(pilot_ids) == 15
    ids = pilot.read_json(pilot.FOLD)["folds"]["D"]["train_case_ids"]
    ordered = pilot_ids + [case for case in ids if case not in prior_hashes]
    assert len(ordered) == len(set(ordered)) == 315 and set(ordered) == set(ids)
    all_rows = {}
    with pilot.MANIFEST.open(encoding="utf-8") as f:
        import json
        for row in map(json.loads, f):
            if row["case_id"] in ids:
                all_rows[row["case_id"]] = row
    sources = Counter(all_rows[k]["source_id"] for k in ordered)
    assert len(sources) == 63 and set(sources.values()) == {5}
    scope = {
        "scope":"D/train", "reused_15_in_original_order":pilot_ids, "new_case_ids":ordered[15:],
        "worker_limit":WORKERS, "replay_code_sha256":pilot.sha(Path(pilot.__file__)),
        "full_entry_sha256":pilot.sha(Path(__file__)), "pilot_scope_sha256":PILOT_SCOPE,
        "pilot_result_sha256":PILOT_RESULT,
        "input_sha256":{str(p.relative_to(pilot.ROOT)):h for p,h in pilot.EXPECTED.items()},
        "full_random_stream":"PCG64 seed 2026112811, advance over 15 pilot cases, then remaining cases in frozen Fold D order, E then J, 8 selections per region",
        "sampler":{"rng":"numpy.default_rng/PCG64","seed":0,"rows":8192,
                   "draws":"weighted face choice then all 8192x2 offsets"},
    }
    if sys.argv[1:] == ["freeze"]:
        OUT.mkdir(exist_ok=False)
        pilot.save(OUT/"pilot_scope.json",scope)
        print("FROZEN",pilot.sha(OUT/"pilot_scope.json"),flush=True)
        return
    assert sys.argv[1:] == ["run"] and pilot.read_json(OUT/"pilot_scope.json") == scope
    assert list(OUT.iterdir()) == [OUT/"pilot_scope.json"]
    import numpy as np
    import psutil
    assert np.__version__ == previous["numpy"]
    prior = [readback(PILOT,case,all_rows[case],prior_hashes[case],np) for case in pilot_ids]
    rng = np.random.Generator(np.random.PCG64(2026112811))
    for rec in prior:
        with np.load(PILOT/rec["sidecar"],allow_pickle=False) as z:
            labels = z["labels_G"]
        for label in (0,1):
            selected_rows = np.sort(rng.choice(np.flatnonzero(labels==label),size=8,replace=False))
            assert selected_rows.tolist() == [x["row"] for x in rec["spot_checks"] if x["is_j"]==bool(label)]
    states = {}
    for case in ordered[15:]:
        states[case] = rng.bit_generator.state
        historical = pilot.read_json(pilot.MANIFEST.parent/"cases"/f"{case}.json")
        for reg in ("G_native_sample_count","G_J_sample_count"):
            rng.choice(np.arange(historical[reg]),size=8,replace=False)
    starts = time.monotonic()
    active = {}
    complete = {}
    peak_worker = 0
    pending = iter(ordered[15:])
    failed = None
    with ProcessPoolExecutor(max_workers=WORKERS, initializer=initialize) as executor:
        for _ in range(WORKERS):
            case = next(pending)
            active[executor.submit(work,all_rows[case],states[case])] = case
        while active:
            done, _ = wait(active,return_when=FIRST_COMPLETED)
            for event in done:
                case = active.pop(event)
                try:
                    record, peak = event.result()
                    complete[case] = record
                    peak_worker = max(peak_worker,peak)
                    if len(complete) % 15 == 0 or len(complete)==1:
                        print(f"PASS {len(complete)}/300 new {case} rss_worker_peak={peak_worker}",flush=True)
                except Exception as exc:
                    failed = failed or {"case_id":case,"error":repr(exc)}
                    print("HOLD", case, repr(exc),flush=True)
            if failed is None:
                for _ in done:
                    case = next(pending,None)
                    if case is not None:
                        active[executor.submit(work,all_rows[case],states[case])] = case
    if failed is not None:
        pilot.save(OUT/"full_result.json",{"status":"P0_HOLD_LABELS","new_completed":len(complete),
                   "new_completed_ids":sorted(complete),**failed})
        sys.exit(1)
    assert len(complete)==300 and set(complete)==set(ordered[15:])
    assets = []
    check_stream = np.random.Generator(np.random.PCG64(2026112811))
    for case in ordered:
        directory = PILOT if case in prior_hashes else OUT
        rec_file = directory/f"{case}.json"
        rec_sha = prior_hashes.get(case) or pilot.sha(rec_file)
        record = readback(directory,case,all_rows[case],rec_sha,np)
        if case in complete:
            assert record == complete[case]
        with np.load(directory/record["sidecar"],allow_pickle=False) as z:
            labels = z["labels_G"]
        for label in (0,1):
            selected_rows = np.sort(check_stream.choice(np.flatnonzero(labels==label),size=8,replace=False))
            assert selected_rows.tolist() == [x["row"] for x in record["spot_checks"] if x["is_j"]==bool(label)]
        assets.append({"case_id":case,"source_id":record["source_id"],
                       "target_sha256":record["target_ordered_fp32_sha256"],
                       "record_path":rec_file.relative_to(HERE).as_posix(),"record_sha256":rec_sha,
                       "label_path":(directory/record["sidecar"]).relative_to(HERE).as_posix(),
                       "label_sha256":record["sidecar_sha256"], "n_E":record["n_E"],"n_J":record["n_J"]})
    assert len(list(OUT.iterdir()))==601
    for p,h in pilot.EXPECTED.items():
        assert pilot.sha(p)==h
    pilot.save(OUT/"label_manifest_v1.json",{"scope_sha256":pilot.sha(OUT/"pilot_scope.json"),"cases":assets})
    records = prior+[complete[k] for k in ordered[15:]]
    fields=("n_E","n_J","k_E","k_J","E_area_mm2","J_area_mm2","J_area_fraction",
            "J_sample_minus_area_pp","FOV_area_mm2","FOV_sample_count","duplicate_target_rows",
            "unique_sampled_faces","world_roundtrip_max_mm","recomputed_frame_mismatched_rows")
    def summary(subset):
        return {k:np.percentile([r[k] for r in subset],[0,5,50,95,100]).tolist() for k in fields}
    result = {
        "status":"P0B_FULL315_PASS","new_replay":300,"reused_pilot":15,"verified_cases":315,
        "verified_sources":len(sources),"target_rows":315*8192,"spot_checks":315*16,
        "new_raw_sha256_checks":300*3,"new_recomputed_frame_different_cases":sum(
             r["recomputed_frame_mismatched_rows"]>0 for r in complete.values()),
        "percentile_order":[0,5,50,95,100],"overall":summary(records),
        "by_defect":{k:summary([r for r in records if r["case_id"].endswith("__"+k)]) for k in pilot.CLASSES},
        "scope_sha256":pilot.sha(OUT/"pilot_scope.json"),
        "label_manifest_sha256":pilot.sha(OUT/"label_manifest_v1.json"),
        "elapsed_seconds":time.monotonic()-starts,"max_observed_single_worker_rss":peak_worker,
        "local_available_bytes_at_end":psutil.virtual_memory().available,
        "cuda_calls":0,"model_forward":0,"optimizer_steps":0,
    }
    pilot.save(OUT/"full_result.json",result)
    print("P0B_FULL315_PASS",pilot.sha(OUT/"full_result.json"),result["elapsed_seconds"],flush=True)


if __name__ == "__main__":
    main()

