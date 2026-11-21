"""Artificial CPU contracts for the P5 predictor and scorer."""

import io
import json
import sys
import tarfile
import unittest
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fcsp_p5_common_v1 as c
import fcsp_p5_predict_v1 as p
import fcsp_p5_score_v1 as s

torch.set_num_threads(2)
p.load_numeric()
s.load_numeric()


def blob(**arrays):
    f=io.BytesIO()
    np.savez_compressed(f,**arrays)
    return f.getvalue()


def record(path, payload):
    path.write_bytes(payload)
    return dict(path=str(path),**c.file_record(path))


def fixture_cases():
    folders=((f,range(lo,lo+21)) for f,lo in (("C",0),("D",21)))
    return [dict(fold=f,case_id=f"train__{n:03d}__{k}",source_id=f"train:{n:03d}",defect=k,
                 cache_sha256="0"*64) for f,ns in folders for n in ns for k in sorted(s.DEFECTS)]


class Contracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        p3=HERE/"P5_server_head_input_index_v1.json"
        cls.idx=json.loads(p3.read_bytes())
        metric=json.loads((HERE/"P5_local_score_input_index_v1.json").read_bytes())["reference_metric_source"]
        cls.metric={}
        exec(compile(c.read(metric,65536),metric["path"],"exec"),cls.metric)
        src=HERE.parent/"fcsp_isolated_implementation_20261120_v1/bcsp_fcsp_head_v1.py"
        cls.head={}
        raw=src.read_bytes()
        if c.sha(raw)!=cls.idx["head"]["sha256"]:
            raise AssertionError("bound head source")
        exec(compile(raw,str(src),"exec"),cls.head)

    def test_request_hash_and_claim_contract(self):
        with TemporaryDirectory(dir=HERE) as tmp:
            root=Path(tmp)
            r,a,n,k=(root/f"{x}.json" for x in ("q","auth","runtime","claim"))
            request=dict(schema="fcsp-p5-predict-request-v1",status="AWAITING_EXPLICIT_USER_AUTHORIZATION",
                         execution_authorized=False,single_attempt=True,automatic_retry=False,
                         launch=dict(request=str(r),authorization=str(a),runtime=str(n),claim=str(k)))
            def put(p,x):
                return record(p,json.dumps(x).encode())["sha256"]
            rh=put(r,request)
            ah=put(a,dict(schema="fcsp-p5-predict-authorization-v1",request_sha256=rh,
                          explicit_user_authorization=True,user_authorization_text="artificial"))
            nh=put(n,dict(schema="fcsp-p5-predict-runtime-v1",request_sha256=rh,authorization_sha256=ah))
            args=SimpleNamespace(request=str(r),request_sha256=rh,authorization=str(a),authorization_sha256=ah,
                                 runtime=str(n),runtime_sha256=nh)
            k.write_text(json.dumps(dict(status="CLAIMED_BEFORE_TMUX",request_sha256=rh)),encoding="ascii")
            self.assertEqual(c.authorize(args,"predict"),request)
            k.write_text("{}",encoding="ascii")
            with self.assertRaisesRegex(ValueError,"attempt claim"):
                c.authorize(args,"predict")

    def test_fixed_metadata_routes_only_development_caches(self):
        rows=[]
        for r in self.idx["cases"]:
            keys=("fold","case_id","source_id","normalization","input_sha256")
            rows.append(dict(**{key:r[key] for key in keys},split="development",
                             checkpoint_sha256=r["donor_checkpoint_sha256"],
                             capture=dict(file=PurePosixPath(r["cache"]["path"]).name,
                                          bytes=r["cache"]["bytes"],sha256=r["cache"]["sha256"])))
        rows += [dict(split="train") for _ in range(630)]
        self.assertEqual(len(p.validate_index(self.idx,rows)),4)
        rows[0]["split"]="train"
        with self.assertRaisesRegex(ValueError,"cache manifest count"):
            p.validate_index(self.idx,rows)

    def test_head_checkpoint_cache_and_tiny_archive_roundtrip(self):
        rng=np.random.default_rng(42)
        with TemporaryDirectory(dir=HERE) as tmp:
            root=Path(tmp); head=self.head
            data=dict(Q=rng.normal(size=(256,3)).astype("float32"),
                      P0=rng.normal(size=(256,32,3)).astype("float32"),
                      H=rng.normal(size=(256,384)).astype("float32"),
                      geometry=rng.normal(size=(256,10)).astype("float32"))
            rec=record(root/"fixture.npz",blob(**data,neighbors=np.zeros((256,8),np.int64),
                                               scale=np.ones((256,),np.float32)))
            row=dict(fold="C",case_id="train__000__bilateral",cache=rec,
                     **{key+"_sha256":c.sha(data[key].tobytes()) for key in ("Q","P0")})
            with self.assertRaisesRegex(ValueError,"ordered anchor"):
                p.read_cache({**row,"P0_sha256":"a"*64})
            head_module=head["PlacementHead"](384,.125)
            with torch.no_grad():
                head_module.net[-1].weight.fill_(.001)
            models={}
            for arm in p.ARMS:
                ck=io.BytesIO()
                torch.save(dict(request_sha256="fixture",fold="C",arm=arm,seed=0,step=3900,
                                state_dict=head_module.state_dict()),ck)
                model=dict(request_sha256="fixture",fold="C",arm=arm,checkpoint=record(root/(arm+".pth"),ck.getvalue()),
                           scale=dict(b_train_fp64=.125,b_train_float32_bytes=head_module.b_train.numpy().tobytes().hex()),
                           final_state_sha256=p.state_sha(head_module))
                models["C",arm]=p.load_model(model,head,torch.device("cpu"))
                with self.assertRaisesRegex(ValueError,"frozen trained state"):
                    p.load_model({**model,"final_state_sha256":"b"*64},head,torch.device("cpu"))
            out=root/"outputs";out.mkdir()
            counts=dict(cases=1,head_forward=2,shared_native=1,donor_forward=0,optimizer_step=0)
            with patch.object(p,"COUNTS",counts):
                p.run_predictions(dict(cases=[row]),models,head,torch.device("cpu"),out,lambda _:None,"fixture")
            with tarfile.open(out/"P5_predictions_v1.tar.gz","r:gz") as t:
                self.assertEqual(len(t.getmembers()),6)
                native=t.extractfile("predictions/C__train__000__bilateral__N.npz").read()
                x=s.read_npz(native,("Q","P0"),exact=True)
                self.assertEqual(x["P0"].tobytes(),data["P0"].tobytes())
                calls=t.extractfile("head_forward_journal.jsonl").read().splitlines()
                self.assertEqual(len(calls),2)
                complete=json.load(t.extractfile("completion.json"))
                self.assertTrue(complete["state_and_rng_equal"])

    def test_weighted_recovery_boundary_and_area_conservation(self):
        w=np.array([1.,99.]);q=np.array([2.1,2.]);d=np.array([2.,3.])
        x=s.region_metrics(self.metric,d,q,d,w,2.1)
        self.assertEqual((x["S0_fraction"],x["Rec"],x["AbsRec"]),(.01,1.,.01))
        self.assertEqual(x["transition_area_mm2"],dict(persistent=0.,recovered=1.,lost=99.,missed=0.))
        y=s.region_metrics(self.metric,d,q,d,np.array([1.,199.]),2.1)
        self.assertIsNone(y["Rec"])
        self.assertEqual(y["AbsRec"],.005)

    def test_native_replays_inherited_metrics_and_pair_risk(self):
        rng=np.random.default_rng(103)
        dense=rng.normal(0,3,(256,32,3)).astype("float32")
        gt=rng.normal(0,3,(8192,3)).astype("float32")
        pts=np.array([[0.,0.,0.],[2.,0.,1.],[.2,1.,.9],[4.5,1.,.3]])
        ref=dict(a_centers=pts,a_weights=np.array([2.,3.,4.,5.]),a_is_j=np.array([False,True,False,True]),
                 a_axes=np.array([0,1,2,0]),affine=np.eye(3),b_centers=pts,b_weights=np.ones(4))
        case=dict(fold="D",case_id="fixture",source_id="fixture",defect="bilateral",
                  normalization=dict(center=[0.,0.,0.],scale=1.))
        outputs=s.score_case(case,dict(Q=dense[:,0],N=dense,
                             **{"B0-Global":dense,"B1-Local":dense+100.}),ref,gt,.1,self.metric)
        native=self.metric["score_cloud"](dense.reshape(-1,3),ref,gt.astype("float64"))
        metrics={}
        for region,x in ((k,native["regions"]["A1"][k]) for k in ("E","J")):
            metrics[region+"_P95_mm"]=x["p95_mm"]
            metrics.update({f"{region}_coverage_{k}mm":v for k,v in x["coverage"].items()})
        ar,_,_=self.metric["a2_reference"](ref)
        metrics.update(CD_L1_mm=native["CD_L1_mm"],
                       reverse_A2_P95_mm=native["reverse_discrete_reference"]["A2"]["p95_mm"],
                       **{"reverse_A2_outlier_20.0mm":float(np.mean(self.metric["nearest"](dense.reshape(-1,3),ar)>20.))})
        old=dict(metrics=metrics,risk_labels=dict(severe_geometry=False))
        s.anchor_replay(outputs["N"],old)
        row=s.pair_case(case,outputs)
        self.assertEqual(row["comparisons"]["B1-Local-N"]["risk"],"01")
        self.assertEqual(row["comparisons"]["B0-Global-N"]["delta"]["CD_L1_mm"],0.)

    def test_archive_schema_and_source_aggregation(self):
        cases=fixture_cases()
        idx=dict(cases=cases,counts=s.COUNTS)
        fake={}
        rows=[];journal=[]
        for x in cases:
            f,k=x["fold"],x["case_id"]
            for a in s.ARMS:
                name=f"predictions/{f}__{k}__{a}.npz"
                fake[name]=b"x"
                rows.append(dict(fold=f,case_id=k,arm=a,member=name,bytes=1,cache_sha256="0"*64))
                if a!="N":
                    journal.append(dict(index=len(journal)+1,fold=f,case_id=k,arm=a,status="CLAIMED_BEFORE_HEAD_FORWARD"))
        fake["prediction_manifest.jsonl"]=b"\n".join(json.dumps(x).encode() for x in rows)
        fake["head_forward_journal.jsonl"]=b"\n".join(json.dumps(x).encode() for x in journal)
        fake["completion.json"]=json.dumps(dict(status="AWAITING_READ_ONLY_PREDICTION_FREEZE_AUDIT",
             request_sha256="fixture",state_and_rng_equal=True,counts=p.COUNTS,
             snapshots={f+"/"+a:"fake" for f in "CD" for a in p.ARMS})).encode()
        tar=io.BytesIO()
        with tarfile.open(fileobj=tar,mode="w") as t:
            for name,b in fake.items():
                item=tarfile.TarInfo(name);item.size=len(b);t.addfile(item,io.BytesIO(b))
        tar.seek(0)
        with tarfile.open(fileobj=tar) as t:
            self.assertEqual(len(s.manifest_lookup(t,idx,"fixture")),630)
            with self.assertRaisesRegex(ValueError,"inference completion"):
                s.manifest_lookup(t,idx,"other")
        paired=[s.pair_case(x,{a:dict(metrics=dict(M=1.,missing=None),severe=False) for a in s.ARMS}) for x in cases]
        sources=s.source_rows(paired)
        self.assertEqual(len(sources),42)
        self.assertEqual(sources[0]["comparisons"]["B1-Local-N"]["delta"],
                         dict(M=dict(mean=0.,cases=5),missing=dict(mean=None,cases=0)))


if __name__=="__main__":
    unittest.main(verbosity=2)
