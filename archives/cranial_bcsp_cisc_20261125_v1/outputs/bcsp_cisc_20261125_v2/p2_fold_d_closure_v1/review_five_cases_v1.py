"""Five-case offline closure review using frozen Native outputs."""
import hashlib
import io
import json
from pathlib import Path
import runpy
import tarfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SCORE = ROOT / "p3_rui_d_cpu_score_v2"
AUDIT = ROOT / "p3_rui_d_native_post_freeze_v1"
ARMS = "RUI"


def read_json(path):
    return json.loads(path.read_bytes())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verified(record):
    path = Path(record["path"])
    assert path.resolve(strict=True) == path
    data = path.read_bytes()
    assert len(data) == record["bytes"] and digest(data) == record["sha256"], path
    return data


def finite(x):
    assert np.isfinite(x).all()
    return x


def matrix(v):
    a, b, c, d, e, f = map(float, v)
    return np.array([[a, d, e], [d, b, f], [e, f, c]])


def draw(cid, category, ref, gt, clouds, a2, metric):
    center = gt.mean(axis=0)
    _, _, directions = np.linalg.svd(gt - center, full_matrices=False)
    projection = directions[:2].T
    for j in range(2):
        if projection[np.argmax(np.abs(projection[:, j])), j] < 0:
            projection[:, j] *= -1

    def project(x):
        return (x - center) @ projection

    j = ref["a_is_j"].astype(bool)
    ec = project(ref["a_centers"][~j])
    jc = project(ref["a_centers"][j])
    extent = np.concatenate([project(ref["a_centers"]),
                             *[project(x) for arm in clouds.values() for x in arm.values()]])
    lower, upper = extent.min(0), extent.max(0)
    margin = max(upper - lower) * .06
    fig, ax = plt.subplots(3, 3, figsize=(10.6, 9.1), constrained_layout=True, sharex=True, sharey=True)
    cols = (("S", "Observed anchors"), ("Q", "Coarse queries"), ("Dense", "Dense prediction"))
    for i, arm in enumerate(ARMS):
        for j, (stage, title) in enumerate(cols):
            panel = ax[i, j]
            panel.scatter(*ec[::max(1, len(ec)//5500)].T, s=1, color="#c2cbd5", alpha=.45, linewidths=0)
            panel.scatter(*jc[::max(1, len(jc)//3600)].T, s=1.8, color="#008c7d", alpha=.42, linewidths=0)
            loc = project(clouds[arm][stage])
            mask = metric.nearest(clouds[arm][stage], a2) > 20 if stage != "S" else np.zeros(len(loc),bool)
            size = 1.7 if stage == "Dense" else 7.2
            panel.scatter(*loc[~mask].T,s=size,color="#304aab",alpha=.6,linewidths=0)
            if mask.any():
                panel.scatter(*loc[mask].T,s=size+1,color="#d34635",alpha=.75,linewidths=0)
            panel.set_aspect("equal")
            panel.set_xlim(lower[0]-margin,upper[0]+margin)
            panel.set_ylim(lower[1]-margin,upper[1]+margin)
            if i == 0:
                panel.set_title(title)
            if j == 0:
                panel.set_ylabel(f"{arm}_D\nPC2 (mm)")
            if i == 2:
                panel.set_xlabel("PC1 (mm)")
            panel.grid(alpha=.14)
    fig.suptitle(f"{cid}  |  {category.replace('_', ' ')}")
    legend = [Line2D([0],[0],marker="o",linestyle="",markersize=5,color=c,label=n)
              for n,c in (("E reference","#c2cbd5"),("J reference","#008c7d"),
                          ("Observed anchor / prediction","#304aab"),("Q/P farther than 20 mm from A2","#d34635"))]
    fig.legend(handles=legend,loc="outside lower center",ncol=4,frameon=False,fontsize=8)
    path = HERE / f"{cid}_stages.png"
    assert not path.exists()
    fig.savefig(path,dpi=145,facecolor="white")
    plt.close(fig)
    return path.name


def main():
    verdict_path = SCORE / "CISC_P2_FoldD_preregistered_decision_v1.json"
    assert digest(verdict_path.read_bytes()) == "42b04616c20f20e421f224d17a8e630981499f76645fc900b36c176823adbc95"
    verdict = read_json(verdict_path)
    frozen_path = SCORE / "formal_post_score_freeze_receipt_v2.json"
    receipt = json.loads(verified(verdict["score_freeze"]))
    score_path = SCORE / "scored_once_v2/model_scores.jsonl"
    scores = {(r["case_id"],r["arm"]):r for r in map(json.loads,
        verified(dict(path=str(score_path),**receipt["artifact_hashes"]["model_scores.jsonl"])).splitlines())}
    q = read_json(SCORE / "CISC_RUI_D_CPU_scoring_execution_request_v2.json")
    assert q["prediction_request_sha256"] == "a05eba8bf496332916d07cfd40a99d698b0cccd83c62e8900cccb091ae05c06b"
    local = json.loads(verified(q["local_archive"]))
    _ = json.loads(verified(q["prediction_freeze"]))
    verified(q["geometry_scoring"])
    verified(q["geometry_metrics"])
    geom = runpy.run_path(str(Path(q["geometry_scoring"]["path"])))
    from types import SimpleNamespace
    metric = SimpleNamespace(**runpy.run_path(str(Path(q["geometry_metrics"]["path"]))))
    cases = {r["case_id"]:r for r in json.loads(verified(q["case_index"]))["cases"]}
    archive = verified(local["archive"])
    stamps = {n:h for h,n in (l.split("  ",1) for l in verified(local["sidecars"]["contents.sha256"]).decode().splitlines())}
    categories = {k:v for k,v in verdict["I_minus_U_severe_case_details"].items()}
    assert {k:len(v) for k,v in categories.items()} == dict(new=2,rescued=2,common=1)
    results = []
    with tarfile.open(fileobj=io.BytesIO(archive),mode="r:gz") as tar:
        for category, items in categories.items():
            for descriptor in items:
                cid = descriptor["case_id"]
                c = cases[cid]
                norm = c["normalization"]
                with np.load(io.BytesIO(verified(c["reference"])),allow_pickle=False) as bank:
                    ref={k:bank[k] for k in bank.files}
                with np.load(io.BytesIO(verified(c["point_file"])),allow_pickle=False) as bank:
                    y=bank["implant"]
                assert digest(y.tobytes()) == c["target_array_sha256"]
                gt=metric.world_points(y,norm)
                a2,*_=metric.a2_reference(ref)
                arrays, clouds, data = {}, {}, {}
                for arm in ARMS:
                    path=f"predictions/{arm}_D__{cid}.npz"
                    raw=tar.extractfile(path).read()
                    assert digest(raw)==stamps[path]
                    with np.load(io.BytesIO(raw),allow_pickle=False) as z:
                        arr={k:z[k] for k in z.files}
                    assert np.array_equal(arr["coarse"],arr["S"]+arr["delta"])
                    assert np.array_equal(arr["parent_index"],np.repeat(np.arange(256),32))
                    clouds[arm]={k:finite(metric.world_points(arr[n],norm)) for k,n in
                                 (("S","S"),("Q","coarse"),("Dense","prediction"))}
                    measured={}
                    for k,v in clouds[arm].items():
                        m,_,_=geom["endpoint"](metric,v,ref,a2,gt,dense=k=="Dense")
                        if k!="S":
                            old=scores[cid,arm]["coarse" if k=="Q" else "dense"]
                            assert all(np.isclose(m[n],old[n],rtol=1e-12,atol=1e-12) for n in old), (cid,arm,k)
                        measured[k]=m
                    arrays[arm]=arr
                    data[arm]=dict(stages=measured, parent_child=scores[cid,arm]["geometry"]["far_parent_child"],
                                   delta_mm_p50_p95=scores[cid,arm]["geometry"]["anchor_delta_mm_p50_p95"],
                                   severe=scores[cid,arm]["severe_geometry"],
                                   mechanism=scores[cid,arm].get("mechanism"),prediction_sha256=stamps[path])
                contrasts={}
                for hi,lo in (("I","U"),("I","R"),("U","R")):
                    a,b=data[hi],data[lo]
                    stage_changes={k:{m:a["stages"][k][m]-b["stages"][k][m]
                                      for m in a["stages"][k]} for k in clouds[hi]}
                    contrasts[f"{hi}_minus_{lo}"]=dict(
                        stages=stage_changes,
                        ordered_anchors_exact=bool(np.array_equal(arrays[hi]["S"],arrays[lo]["S"])),
                        centroid_separation_mm={k:float(np.linalg.norm(clouds[hi][k].mean(0)-clouds[lo][k].mean(0)))
                                                for k in clouds[hi]})
                image=draw(cid,category,ref,gt,clouds,a2,metric)
                results.append(dict(case_id=cid,category=category,arms=data,contrasts=contrasts,figure=image,
                                    figure_sha256=digest((HERE/image).read_bytes())))
                print(cid,category,flush=True)
    artifact=HERE/"five_case_offline_review_v1.json"
    with artifact.open("x",encoding="utf-8",newline="\n") as f:
        json.dump(dict(case_count=len(results),prediction_inputs=15,additional_forward=0,cases=results,
                       score_freeze_sha256=digest(frozen_path.read_bytes()), verdict_sha256=digest(verdict_path.read_bytes()),
                       archive_sha256=local["archive"]["sha256"],method="Native S/Q/Dense; frozen A1 E/J, four A2 subpoints per face, world mm"),
                  f,indent=2,allow_nan=False)
        f.write("\n")
    print(digest(artifact.read_bytes()),flush=True)


if __name__ == "__main__":
    main()
