"""Local synthetic check of the CUDA worker's call and authorization contracts."""
import copy
import hashlib
import json
from pathlib import Path
import re
import sys
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import torch
from torch import nn

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bcsp_scq_prime_cuda_admission_v1 as entry


def require_failure(action):
    try:
        action()
    except RuntimeError:
        return
    raise AssertionError("expected rejection")


class Fixture(nn.Module):
    def __init__(self, arm):
        super().__init__()
        self.arm = arm
        self.linear = nn.Linear(3, 3)
        self.bn = nn.BatchNorm1d(3)
        self.base_model = nn.Module()
        if arm != "B":
            self.base_model.scq = nn.Module()
            self.base_model.scq.W1 = nn.Linear(3, 4)
            self.base_model.scq.W2 = nn.Linear(4, 3)
            nn.init.zeros_(self.base_model.scq.W2.weight)
            nn.init.zeros_(self.base_model.scq.W2.bias)

    def forward(self, x):
        batch = x.shape[0]
        q = self.bn(self.linear(x[:, :1]).transpose(1, 2)).transpose(1, 2)
        raw = q.expand(batch, 256, 3)
        if self.arm != "B":
            h = self.base_model.scq
            delta = h.W2(torch.nn.functional.gelu(h.W1(q))).expand_as(raw)
            used = raw + delta
            self.base_model._scq_last_info = dict(Q0=raw, Qused=used, delta=delta)
        else:
            used = raw
        dense = used[:, :1].expand(batch, 8192, 3)
        return (used, used[:, :0], dense[:, :0], dense) if self.training else (used, dense)

    def get_loss(self, ret, target, **kwargs):
        return ret[0].new_zeros(()), (ret[-1] - target).square().mean()


def state_sha(model, parameters_only=False):
    tensors = dict(model.named_parameters()) if parameters_only else model.state_dict()
    return hashlib.sha256(b"".join(t.detach().numpy().tobytes() for t in tensors.values())).hexdigest()


def main():
    torch.set_num_threads(2)
    digest, auth_sha = "a"*64, "b"*64
    ident = dict(gpu_uuid="GPU-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee", python_realpath="/opt/conda/bin/python3")
    q = dict(schema="bcsp-scq-prime-artificial-cuda-v1", status="AWAITING_EXPLICIT_USER_AUTHORIZATION",
             execution_authorized=False, science=entry.SCIENCE, phases=[list(p) for p in entry.PHASES],
             limits=entry.LIMITS, fixture=entry.FIXTURE, tolerances=entry.TOLERANCE, identity=ident,
             readiness=dict(status="BOUND_FOR_FRESH_REVERIFICATION", fresh_reverification_required=True),
             environment=dict(CUDA_VISIBLE_DEVICES=ident["gpu_uuid"]), fold="C", seed=2026112101,
             initialization=dict(seed=2026112101), real_data_allowlist=[], checkpoint_allowlist=[])
    auth = dict(schema="bcsp-scq-prime-cuda-authorization-v1", request_sha256=digest,
                explicit_user_authorization=True, user_authorization_text="Artificial fixture grant")
    runtime = dict(schema="bcsp-scq-prime-cuda-runtime-v1", request_sha256=digest, authorization_sha256=auth_sha)
    assert entry.authorize(q, digest, auth, auth_sha, runtime) is q
    for key, value in (("seed", 0), ("checkpoint_allowlist", ["x"]), ("status", "AWAITING_CURRENT_RESOURCE_BINDING")):
        bad = copy.deepcopy(q)
        bad[key] = value
        require_failure(lambda: entry.authorize(bad, digest, auth, auth_sha, runtime))
    require_failure(lambda: entry.authorize(q, digest, dict(auth, request_sha256=auth_sha), auth_sha, runtime))
    require_failure(lambda: entry.authorize(q, digest, auth, auth_sha, dict(runtime, authorization_sha256=digest)))

    root = "/home/jovyan/adapointr_work/PoinTr"
    out = root + "/logs/cranial_bcsp_fullmamba/SCQ_PRIME_artificial"
    control = root + "/third_party/scq_prime/control"
    paths = {k+"_path":control+"/"+k+".json" for k in ("request", "authorization", "runtime")}
    script = entry.render_launcher(dict(q, output=out, project=root, launch_contract=paths,
                                        entry=dict(path=control+"/entry.py")), digest, auth_sha, "c"*64)
    assert "mkdir -p "+out.rsplit("/",1)[0] in script
    assert script.index("mkdir "+out) < script.index(" >"+out+"/launch.log")
    assert max(len(line.encode()) for line in script.splitlines()) <= 2048 and 'exit "$rc"' in script

    counts, events = entry.counters(), []
    rng = torch.get_rng_state().clone()
    x = torch.linspace(0.1, 0.8, 8).reshape(8, 1, 1).expand(8, 8192, 3)
    target = torch.ones_like(x) * 3
    helper = SimpleNamespace(state_sha=state_sha)
    parent = SimpleNamespace(rng_state=lambda *args: hashlib.sha256(torch.get_rng_state().numpy().tobytes()).hexdigest())
    ref = None
    with patch.multiple(torch.cuda, synchronize=lambda: None, get_rng_state=lambda _: rng,
                        set_rng_state=lambda *_: None), patch.object(entry, "gradient_prefixes", return_value=("linear",)):
        for phase in entry.PHASES:
            torch.manual_seed(2026112101)
            model = Fixture(phase[1])
            result, baseline = entry.phase_checks(torch,np,model,helper,parent,x,target,phase,ref,counts,events.append,lambda *_:None)
            if baseline is not None:
                ref = baseline
            assert (result["loss"] is not None) is phase[3]
    assert counts == {k:entry.SCIENCE[k] for k in counts}
    attempts = [v["operation"] for v in events if v.get("kind") == "ATTEMPT_BEFORE_CALL"]
    assert attempts == ["full_forward"]*3 + ["full_forward","full_loss","full_backward"]*3
    assert sum(v.get("kind")=="PHASE_RESTORATION" and v["state_restored"] and v["RNG_restored"] for v in events)==6
    require_failure(lambda: entry.claim(counts,"full_forward",events.append))
    source = Path(entry.__file__).read_bytes()
    assert not re.search(rb"torch\.optim|optimizer\.step\(", source)
    print(json.dumps(dict(status="PASS",counts=counts,confirmed_restorations=6,
                          authorization_rejections=5,launcher_max_line=max(map(len,script.splitlines())))))


if __name__ == "__main__":
    main()
