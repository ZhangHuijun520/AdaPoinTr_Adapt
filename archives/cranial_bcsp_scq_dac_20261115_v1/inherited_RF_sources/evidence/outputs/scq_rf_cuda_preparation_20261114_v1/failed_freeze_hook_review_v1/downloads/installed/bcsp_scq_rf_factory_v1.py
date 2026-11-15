"""Reuse the exact SCQ forward; substitute Q2 at its existing coarse handoff."""
import types
import torch
import bcsp_scq_factory_v1 as parent
from bcsp_scq_rf_residual_v1 import RFResidual, require


def install(model, variant, initialization):
    require(variant in ('RF-Static', 'RF-Requery'), 'RF variant')
    b = model.base_model
    require(hasattr(b, 'scq') and b.scq.variant == 'S' and not hasattr(b, 'rf'), 'RF needs unmodified S')
    require(getattr(b.scq.forward, '__func__', None) is type(b.scq).forward, 'SCQ forward already adapted')
    before = {k: parent.parent.parent.tensor_sha(v) for k, v in model.state_dict().items()}
    rng = torch.random.get_rng_state().clone()
    b.rf = RFResidual(variant, b.decoder.knn, initialization)
    first_forward, feedback = b.scq.forward, b.rf

    def two_stage(scq, M, F, z, Qraw):
        Q1, first = first_forward(M, F, z, Qraw)
        # Only integer N0 comes from the detached diagnostic. Q1 remains graph-bearing.
        Q2, second = feedback(M, F, z, Q1, first['indices'])
        record = dict(first)
        record.update(Qused=Q2.detach(), delta=(Q2 - Qraw).detach(),
                      Q1=Q1.detach(), delta0=first['delta'],
                      delta1=second['delta1'], N0=first['indices'], N1=second['indices'])
        return Q2, record

    b.scq.forward = types.MethodType(two_stage, b.scq)
    require(torch.equal(rng, torch.random.get_rng_state()), 'RF construction changed parent RNG')
    require(all(parent.parent.parent.tensor_sha(model.state_dict()[k]) == v for k, v in before.items()), 'RF common state changed')
    require(sum(x.numel() for x in b.rf.parameters()) == 231171, 'RF exact parameter delta')
    parent.parent.no_attention_inventory(model)
    return model, dict(variant=variant, additional_parameters=231171,
                       common_state_preserved=True, CPU_RNG_preserved=True,
                       initialization_sha256=initialization['sha256'],
                       total_parameters=sum(x.numel() for x in model.parameters()),
                       handoff='original SCQ coarse return before query MLP; Q2 to all original consumers')


def build_model(legacy_builder, variant, scq_initialization, rf_initialization, seed=0):
    model, original = parent.build_model(legacy_builder, 'S', scq_initialization, seed)
    model, evidence = install(model, variant, rf_initialization)
    return model, dict(parent=original, rf=evidence)


def build_artificial_fixture(legacy_builder, mixer_builder, variant, scq_initialization, rf_initialization):
    model, original = parent.build_artificial_fixture(legacy_builder, mixer_builder, 'S', scq_initialization)
    model, evidence = install(model, variant, rf_initialization)
    return model, dict(parent=original, rf=evidence, artificial_fixture=True)


def optimizer_groups(model, shared_parent_groups):
    """Apply the existing SCQ grouping unchanged, then classify only the RF tensors."""
    head = model.base_model.rf
    rf_ids = {id(p) for p in head.parameters()}
    # Existing SCQ policy sees a parameter view excluding RF, without unregistering it.
    class ParentView:
        base_model = model.base_model
        def parameters(self):
            return (p for p in model.parameters() if id(p) not in rf_ids)
    groups = parent.optimizer_groups(ParentView(), shared_parent_groups)
    return [*groups, dict(params=[head.V1.weight, head.V2.weight], weight_decay=5e-4),
            dict(params=[head.V1.bias, head.V2.bias], weight_decay=0.)]
