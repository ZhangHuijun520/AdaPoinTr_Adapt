"""SCQ-PRIME construction and lifecycle boundary for a separately admitted caller."""
import argparse
import hashlib
import json
from pathlib import Path
import random

SEEDS = (2026112101, 2026112102)
ARMS = ("B", "F", "S")
FOLDS = ("C", "D")
PROJECTION_SHA = "495bf59bc8ee068fe5a2892c6545796404ad1d81cb7b5862a8c09e9491eb7589"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def identity(variant, fold, seed):
    require(variant in ARMS and fold in FOLDS and type(seed) is int and seed in SEEDS, "PRIME arm/fold/seed")
    return dict(variant=variant, fold=fold, seed=seed)


def parse_identity(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", dest="variant", choices=ARMS, required=True)
    parser.add_argument("--fold", choices=FOLDS, required=True)
    parser.add_argument("--seed", type=int, choices=SEEDS, required=True)
    return identity(**vars(parser.parse_args(argv)))


def initializer_bytes(torch, seed, projection):
    require(type(seed) is int and seed in SEEDS, "registered initializer seed")
    require(len(projection) == 10752 and hashlib.sha256(projection).hexdigest() == PROJECTION_SHA, "original Pfix bytes")
    generator = torch.Generator(device="cpu").manual_seed(seed)
    bound = 1802 ** -0.5
    weight = torch.empty((384, 1802), dtype=torch.float32, device="cpu").uniform_(-bound, bound, generator=generator)
    bias = torch.empty(384, dtype=torch.float32, device="cpu").uniform_(-bound, bound, generator=generator)
    zero_output_layer = bytes((3 * 384 + 3) * 4)
    return (weight.numpy().astype("<f4", copy=False).tobytes() + bias.numpy().astype("<f4", copy=False).tobytes()
            + zero_output_layer + projection)


def construct(run, legacy_builder, initialization, *, torch, np, parent, lqi, scq, artificial_mixer=None):
    run = identity(**run)
    variant, seed = run["variant"], run["seed"]
    artificial = artificial_mixer is not None
    if variant != "B":
        require(initialization["seed"] == seed, "head initializer seed binding")
        raw = Path(initialization["path"]).read_bytes()
        require(hashlib.sha256(raw[-10752:]).hexdigest() == PROJECTION_SHA, "original Pfix bytes")
        require(len(raw) == initialization["bytes"] and hashlib.sha256(raw).hexdigest() == initialization["sha256"],
                "head initializer identity")
    else:
        require(initialization is None, "B must not bind an additional head")
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    mixer = artificial_mixer if artificial else parent.native_mixer
    model, evidence = parent._build(legacy_builder, "M0", seed, mixer, artificial_fixture=artificial)
    require(evidence["seed"] == seed, "constructor seed mismatch")
    model, lqi_evidence = lqi._install(model, evidence, mixer, artificial)
    model, scq_evidence = scq.install(model, variant, initialization)
    common = {name: parent.tensor_sha(tensor) for name, tensor in model.state_dict().items()
              if not name.startswith("base_model.scq.")}
    common_sha = hashlib.sha256(json.dumps(common, sort_keys=True).encode()).hexdigest()
    return model, dict(run_identity=run, common_initial_state_SHA256=common_sha, lqi=lqi_evidence, scq=scq_evidence)


def train_admitted(run, model, construction, runtime, runtime_sha, expected_common, admission, device, *args, **kwargs):
    """Keep the CUDA-only execution boundary and pass identity into native serialization."""
    run = identity(**run)
    require(admission["status"] == "SCQ_PRIME_NATIVE_CUDA_ADMISSION_PASS", "PRIME CUDA admission required")
    require(str(device) in ("cuda", "cuda:0") and not model.f0_evidence["artificial_fixture"],
            "native model and CUDA required")
    require(construction["run_identity"] == run and construction["common_initial_state_SHA256"] == expected_common,
            "run or common initialization identity mismatch")
    require(hashlib.sha256(Path(runtime.__file__).read_bytes()).hexdigest() == runtime_sha, "runtime source identity")
    groups = runtime.optimizer_groups(model)[1]
    new = {row["name"]: row["weight_decay"] for row in groups if row["name"].startswith("base_model.scq.")}
    expected = {"base_model.scq.W1.weight": .0005, "base_model.scq.W2.weight": .0005,
                "base_model.scq.W1.bias": 0., "base_model.scq.W2.bias": 0.}
    require(new == ({} if run["variant"] == "B" else expected), "SCQ optimizer groups")
    return runtime.train_lifecycle(model, *args, device=device, run_identity=run, **kwargs)
