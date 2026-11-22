"""Exercise PRIME wiring through the inherited model graph with artificial operators."""
import argparse
import ast
from functools import partial
import gc
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
import types

import numpy as np
import torch
from torch import nn

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
OLD = R / "outputs/cranial_bcsp_scq_implementation_20261113_v1"
P = R / "outputs/cranial_bcsp_mamba_p1_20261104/minimal_implementation_v1"
L = R / "outputs/cranial_bcsp_fullmamba_20261110/lqi_implementation_v1"
SNAP = R / "deliverables/cranial_bcsp_mamba_P1_20261106_v2/payload/parent_source_snapshot"
sys.path[:0] = [str(HERE), str(OLD), str(L), str(P)]
import bcsp_scq_prime_entry_v1 as entry
import bcsp_scq_prime_seeded_parent_v1 as parent
import bcsp_scq_factory_v1 as scq


def artificial_fixture():
    # Reuse the original adapter's KNN and the same legacy artificial model construction.
    tree = ast.parse((SNAP / "tools/bcsp_adapter.py").read_text(encoding="utf-8"))
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ("_shape_check", "torch_knn")]
    adapter = {"torch": torch}
    exec(compile(ast.Module(nodes, []), str(SNAP / "tools/bcsp_adapter.py"), "exec"), adapter)
    knn = adapter["torch_knn"]
    # Exact computational classes, full mother forward and loss; constructors below are artificial.
    env=dict(torch=torch,nn=nn,partial=partial,trunc_normal_=nn.init.trunc_normal_,knn_point=knn,chamfer=None)
    env['index_points']=lambda pts,ix:pts[torch.arange(pts.shape[0]).reshape(-1,*([1]*(ix.ndim-1))),ix]
    def extract(path,classes=(),functions=()):
     t=ast.parse(path.read_text(encoding='utf-8'));nodes=[n for n in t.body if isinstance(n,ast.ClassDef) and n.name in classes or isinstance(n,ast.FunctionDef) and n.name in functions]
     assert len(nodes)==len(classes)+len(functions)
     for n in nodes:
      if isinstance(n,ast.ClassDef):n.decorator_list=[]
     exec(compile(ast.Module(nodes,[]),str(path),'exec'),env)
    extract(SNAP/'models/Transformer_utils.py',['Mlp','Attention','CrossAttention','DynamicGraphAttention','LayerScale'])
    extract(SNAP/'models/AdaPoinTr.py',['CrossAttnBlockApi','TransformerDecoder','PointTransformerDecoder','SimpleRebuildFCLayer','PCTransformer','AdaPoinTr'])
    extract(SNAP/'extensions/chamfer_dist/__init__.py',['ChamferDistanceL1','ChamferDistanceL1Directional'],['_torch_chamfer_forward'])
    extract(R/'outputs/cranial_bcsp_fullmamba_20261110/implementation_v1/test_f0_cpu_v1.py',['ArtificialCausalMixer','EncoderFixture'])
    # Prior fixture EncoderFixture resolves the exact extracted computational classes here.
    env['env']=env
    class Grouper(nn.Module):
     def forward(self,xyz,n):return xyz[:,:256],xyz[:,:256]
    class Encoder(nn.Module):
     def __init__(self):
      super().__init__();self.blocks=nn.Module();self.blocks.blocks=nn.ModuleList([env['EncoderFixture'](i) for i in range(6)])
     def forward(self,x,pos):
      for b in self.blocks.blocks:x=b(x,pos)
      return x
    class IdentityAdapter(nn.Module):
     def forward(self,x,pos):return x
    fps_calls=[]
    env['misc']=types.SimpleNamespace(fps=lambda xyz,n:(fps_calls.append(n) or xyz[:,:n]))
    def legacy():
     m=env['AdaPoinTr'].__new__(env['AdaPoinTr']);nn.Module.__init__(m)
     b=env['PCTransformer'].__new__(env['PCTransformer']);nn.Module.__init__(b);m.base_model=b
     b.full_instrumentation_enabled=False;b._last_full_instrumentation=None;b.scqr_contract=types.SimpleNamespace(enabled=False,contact_supervision_enabled=False)
     b.query_selection='learned_only';b.num_query=256;b.center_num=[512,256];b.rim_query_enabled=False;b.use_denoise=False;b.scqr_local_geometry=None;b.scqr_query_conditioner=None
     b.grouper=Grouper();b.pos_embed=nn.Linear(3,384);b.input_proj=nn.Linear(3,384);b.encoder=Encoder();b.encoder_adapter=IdentityAdapter()
     b.increase_dim=nn.Sequential(nn.Linear(384,1024),nn.GELU(),nn.Linear(1024,1024));b.mem_link=nn.Identity()
     b.coarse_pred=nn.Sequential(nn.Linear(1024,1024),nn.GELU(),nn.Linear(1024,768))
     b.mlp_query=nn.Sequential(nn.Linear(1027,1024),nn.GELU(),nn.Linear(1024,1024),nn.GELU(),nn.Linear(1024,384))
     b.decoder=env['PointTransformerDecoder'](embed_dim=384,depth=8,num_heads=6,mlp_ratio=2,k=8,self_attn_block_style_list=['attn-graph']+['attn']*7,cross_attn_block_style_list=['attn-graph']+['attn']*7)
     m.full_instrumentation_enabled=False;m._last_full_instrumentation=None;m.decoder_type='fc';m.factor=32;m.num_query=256;m.denoise_weight=0.;m.fine_coverage_weight=1.;m.fine_local_weight=0.
     for name in ['coarse_geometry_guard_enabled','local_rim_guard_enabled','moment_trust_enabled','dense_contact_enabled','rim_query_enabled']:setattr(m,name,False)
     m.scqr_contract=b.scqr_contract
     m.increase_dim=nn.Sequential(nn.Conv1d(384,1024,1),nn.BatchNorm1d(1024),nn.LeakyReLU(.2),nn.Conv1d(1024,1024,1))
     m.reduce_map=nn.Linear(1411,384);m.decode_head=env['SimpleRebuildFCLayer'](768,32)
     m.loss_func=env['ChamferDistanceL1']();m.fine_loss_func=env['ChamferDistanceL1Directional']()
     return m
    return legacy, env["ArtificialCausalMixer"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    out = parser.parse_args().output
    out.mkdir()
    checks, observed = [], {}
    def check(name, condition):
        assert condition, name
        checks.append(name)

    torch.set_num_threads(2)
    legacy, mixer = artificial_fixture()
    original = (OLD / "initialization_v1.bin").read_bytes()[-10752:]
    inp = torch.randn(1, 8192, 3, generator=torch.Generator().manual_seed(118)) * .5
    try:
        for seed in entry.SEEDS:
            raw = entry.initializer_bytes(torch, seed, original)
            file = out / f"artificial_initializer_{seed}.bin"
            file.write_bytes(raw)
            rec = dict(path=str(file), seed=seed, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
            models = {}
            for arm in entry.ARMS:
                run = entry.parse_identity(["--arm", arm, "--fold", "C", "--seed", str(seed)])
                constructor_seeds = []

                def observe_constructor():
                    constructor_seeds.append(torch.initial_seed())
                    return legacy()

                model, proof = entry.construct(run, observe_constructor, None if arm == "B" else rec,
                                               torch=torch, np=np, parent=parent, lqi=scq.parent,
                                               scq=scq, artificial_mixer=mixer)
                check(f"{seed}/{arm} parsed and delivered to parent", proof["run_identity"] == run
                      and proof["lqi"]["parent"]["seed"] == seed and constructor_seeds == [seed])
                check(f"{seed}/{arm} common training RNG", torch.initial_seed() == seed
                      and int(np.random.get_state()[1][0]) == seed
                      and random.getstate() == random.Random(seed).getstate())
                check(f"{seed}/{arm} actual variant", (not hasattr(model.base_model, "scq") if arm == "B"
                      else model.base_model.scq.variant == arm))
                if arm != "B":
                    head = model.base_model.scq
                    head_state = {n: parent.tensor_sha(t) for n,t in head.state_dict().items()}
                    check(f"{seed}/{arm} fixed Pfix bytes",
                          hashlib.sha256(head.Pfix.numpy().tobytes()).hexdigest() == entry.PROJECTION_SHA)
                else:
                    head_state = {}
                with torch.inference_mode():
                    pred = tuple(x.detach().clone() for x in model.eval()(inp))
                check(f"{seed}/{arm} dense shape", pred[1].shape == (1,8192,3))
                models[arm] = (proof, head_state, pred)
                del model
                gc.collect()
            b,f,s = (models[a] for a in entry.ARMS)
            check(f"{seed} all common fingerprints equal", len({m[0]["common_initial_state_SHA256"] for m in models.values()}) == 1)
            check(f"{seed} F/S full head state equal", f[1] == s[1])
            check(f"{seed} B/F/S initial coarse and dense equal",
                  all(torch.equal(x,y) and torch.equal(x,z) for x,y,z in zip(b[2],f[2],s[2])))
            observed[str(seed)] = dict(common=b[0]["common_initial_state_SHA256"], W1=s[1]["W1.weight"], Pfix=entry.PROJECTION_SHA)
        check("different seeds change common state", len({v["common"] for v in observed.values()})==2)
        check("different seeds change W1", len({v["W1"] for v in observed.values()})==2)
        try:
            entry.construct(entry.identity("F","D",entry.SEEDS[0]), legacy, rec, torch=torch, np=np,
                            parent=parent, lqi=scq.parent, scq=scq, artificial_mixer=mixer)
        except ValueError as error:
            check("reject cross-seed initializer", str(error) == "head initializer seed binding")
        else:
            raise AssertionError("accepted wrong initializer seed")
        try:
            entry.identity("B","C",0)
        except ValueError:
            check("reject legacy seed0", True)
        else:
            raise AssertionError("accepted historical seed")
        runtime = types.SimpleNamespace(__file__=str(HERE / "bcsp_scq_prime_runtime_v1.py"))
        model = types.SimpleNamespace(f0_evidence={"artificial_fixture": True})
        try:
            entry.train_admitted(entry.identity("B", "C", entry.SEEDS[0]), model, {}, runtime, "", "",
                                 {"status": "SCQ_PRIME_NATIVE_CUDA_ADMISSION_PASS"}, "cpu")
        except ValueError as error:
            check("reject artificial or CPU lifecycle", str(error) == "native model and CUDA required")
        else:
            raise AssertionError("accepted artificial lifecycle")
    finally:
        (out / "result.json").write_text(json.dumps(dict(checks=checks, observed=observed), indent=2),encoding="utf-8")
    print(f"{len(checks)} artificial CPU checks passed")


if __name__ == "__main__":
    main()
