"""Regression for the exact Fold D development storage root, using metadata only."""
import copy
import hashlib
import json
from pathlib import Path
import runpy


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CURRENT = HERE / "bcsp_scq_fv_BF_D_native_v2.py"
PREVIOUS = ROOT / "foldD_BF_native_prediction_implementation_v1/bcsp_scq_fv_BF_D_native_v1.py"
OLD_ROOT = b"/home/jovyan/adapointr_work/PoinTr/data/bcsp_geov1_foldd_8192_seed0_v1"
VERIFIED_ROOT = b"/home/jovyan/adapointr_work/PoinTr/data/bcsp_geov1_foldc_8192_seed0_v1"
READBACK = ROOT / "foldD_BF_native_prediction_pending_v1/BF_D_native_development_path_readback_v2.json"
READINESS = ROOT / "foldD_BF_native_prediction_readiness_v1.json"


def read_pinned(path, digest):
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == digest, path
    return raw


def main():
    previous = read_pinned(PREVIOUS, "399ac30f2628575eabbf2d6accad86ff9f4ec44bca19ed9e79b9a035e3a40201")
    current = CURRENT.read_bytes()
    assert previous.count(OLD_ROOT) == 1 and current == previous.replace(OLD_ROOT, VERIFIED_ROOT)
    native = runpy.run_path(str(CURRENT))
    r = json.loads(read_pinned(READBACK, "708ac7050de5b441eac13c8b2788b0b6c3093af161f8c4934464f3e9c5031797"))
    ready = json.loads(read_pinned(READINESS, "0fadf7abc5519e74f1e277fa95a69bf7c8e1778f587eb541385e7e2e31aabcc1"))
    binding, manifest = (read_pinned(Path(ready["metadata_bindings"][k]["path"]), ready["metadata_bindings"][k]["sha256"])
                         for k in ("fold", "manifest_8192"))
    folds = json.loads(binding)
    metadata = [json.loads(line) for line in manifest.splitlines()]
    by_case = {m["case_id"]: m for m in metadata}
    rows = []
    for v in r["verified_inputs"]:
        case = v["case_id"]
        m = by_case[case]
        rows.append(dict(case_id=case, source_id=m["source_id"], defect_type=case.rsplit("__",1)[1],
                         n_input=8192, n_output=8192, normalization=m["normalization"],
                         normalization_source=m["normalization_source"],
                         input={k:v[k] for k in ("path","bytes","sha256")}))
    index = dict(fold="D", seed=2026112101, arms=["B","F"], cases=105, sources=21, inputs=rows)
    assert len(native["validate_index"](index, folds, metadata)) == 105
    wrong_root = copy.deepcopy(index)
    path = wrong_root["inputs"][0]["input"]["path"]
    wrong_root["inputs"][0]["input"]["path"] = path.replace(VERIFIED_ROOT.decode(), OLD_ROOT.decode())
    try:
        native["validate_index"](wrong_root, folds, metadata)
    except ValueError as error:
        assert "development input identity" in str(error)
    else:
        raise AssertionError("unverified input root accepted")
    result = dict(status="ARTIFICIAL_CPU_PASS", checks={"verified_root_accepted_and_previous_root_rejected":True},
                  cases=105, real_arrays_loaded=0, forward_calls=0, server_writes=0)
    with (HERE/"cpu_path_regression_result_v2.json").open("x",encoding="ascii",newline="\n") as stream:
        json.dump(result,stream,indent=2)
        stream.write("\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
