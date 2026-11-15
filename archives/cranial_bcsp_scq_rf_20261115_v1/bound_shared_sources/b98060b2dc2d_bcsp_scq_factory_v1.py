"""Install SCQ after the frozen LQI factory; inherited modules keep their paths."""
import hashlib,types
from pathlib import Path
import torch
from torch import nn
import bcsp_lqi_factory_v1 as parent
from bcsp_scq_residual_v1 import SCQResidual,require

MOTHER_SHA256='1f3eb07ad0c3e2f78756682dcb273d745939dc7efda5563c6528915d6d89a1d4'

def install(model,variant,initialization):
    require(variant in ('B','F','S'),'B/F/S only')
    b=model.base_model
    require(not hasattr(b,'scq'),'SCQ already installed')
    require(b.query_selection=='learned_only' and b.num_query==256 and not b.rim_query_enabled and not b.use_denoise,'fixed query contract')
    require(isinstance(b.mem_link,nn.Identity) and b.scqr_local_geometry is None and b.scqr_query_conditioner is None,'fixed Memory and no SCQR')
    require(model.decoder_type=='fc' and model.factor==32 and model.denoise_weight==0 and model.fine_coverage_weight==1 and model.fine_local_weight==0,'fixed original head and loss')
    require(all(not getattr(model,k,False) for k in ['coarse_geometry_guard_enabled','local_rim_guard_enabled','moment_trust_enabled','dense_contact_enabled','rim_query_classification_enabled']),'other objective disabled')
    require(not hasattr(model,'h2_head') and not hasattr(b,'h2_head'),'no H2')
    original=b.forward.__func__
    require(original is type(b).forward,'parent forward must be unmodified')
    source=Path(original.__code__.co_filename)
    require(hashlib.sha256(source.read_bytes()).hexdigest()==MOTHER_SHA256,'exact mother forward source')
    before={n:parent.parent.tensor_sha(t) for n,t in model.state_dict().items()}
    rng=torch.random.get_rng_state().clone()
    if variant!='B':
        b.scq=SCQResidual(variant,b.decoder.knn,initialization)
        adapted=types.FunctionType(_scq_base_forward.__code__,original.__globals__,name='forward')
        b.forward=types.MethodType(adapted,b)
        b._scq_last_info=None
    after=model.state_dict()
    require(all(n in after and parent.parent.tensor_sha(after[n])==v for n,v in before.items()),'common initialization changed')
    require(torch.equal(rng,torch.random.get_rng_state()),'common RNG changed')
    parent.no_attention_inventory(model)
    evidence=dict(version='SCQ-v2-implementation-v1',variant=variant,common_initialization_preserved=True,common_tensor_count=len(before),new_parameters=0 if variant=='B' else sum(p.numel() for p in b.scq.parameters()),initialization_sha256=None if variant=='B' else initialization['sha256'],mother_sha256=MOTHER_SHA256,total_parameters=sum(p.numel() for p in model.parameters()))
    require(evidence['new_parameters']==(0 if variant=='B' else 693507),'SCQ parameter count')
    return model,evidence

def build_model(legacy_builder,variant,initialization,seed=0):
    model,evidence=parent.build_model(legacy_builder,seed)
    model,scq=install(model,variant,initialization)
    return model,dict(parent=evidence,scq=scq)

def build_artificial_fixture(legacy_builder,mixer_builder,variant,initialization):
    model,evidence=parent.build_artificial_fixture(legacy_builder,mixer_builder)
    model,scq=install(model,variant,initialization)
    return model,dict(parent=evidence,scq=scq,artificial_fixture=True)

def optimizer_groups(model,parent_groups):
    """Parent grouping policy remains external; classify only the four new tensors."""
    require(hasattr(model.base_model,'scq'),'SCQ groups require F/S')
    added=list(model.base_model.scq.parameters());ids={id(p) for p in added}
    expected={id(p) for p in model.parameters() if p.requires_grad and id(p) not in ids}
    existing=[p for g in parent_groups for p in g['params']]
    require(len(existing)==len({id(p) for p in existing}) and {id(p) for p in existing}==expected,'parent groups exact shared partition')
    h=model.base_model.scq
    return [*parent_groups,dict(params=[h.W1.weight,h.W2.weight],weight_decay=5e-4),dict(params=[h.W1.bias,h.W2.bias],weight_decay=0.)]


def _scq_base_forward(self, xyz, epoch=None):
    if self.full_instrumentation_enabled and self.training:
        raise RuntimeError(
            'Full-model instrumentation is inference-only; call eval() first'
    )
    if self.training and self.scqr_contract.enabled and epoch is None:
        raise ValueError('SCQR training forward requires an explicit epoch')
    bs = xyz.size(0)
    coor, proxy_features, encoder_pre_adapter, x = (
        self.encode_rim_proxy_tokens(xyz)
    )
    pe = proxy_features[..., x.shape[-1]:]
    encoder_post_adapter = x
    encoder_post_scqr = x
    scqr_aux = None
    if self.scqr_local_geometry is not None:
        local_output = self.scqr_local_geometry(
            x,
            coor,
            xyz,
            epoch=epoch,
        )
        x = local_output.features
        contact_logits, contact_probability = self.scqr_contact_head(x, pe)
        scqr_aux = {
            "protocol_version": "cranial-scqr-v1.1",
            "variant": self.scqr_contract.variant,
            "proxy_coordinates": coor,
            "knn32_indices": local_output.knn32_indices,
            "knn32_radius_normalized": (
                local_output.knn32_radius_normalized.detach()
            ),
            "local_embedding": local_output.local_embedding.detach(),
            "local_residual": local_output.residual.detach(),
            "local_warmup": local_output.warmup,
            "contact_logits": contact_logits,
            "contact_probability": contact_probability,
        }
        encoder_post_scqr = x
    global_feature = self.increase_dim(x) # B 1024 N 
    global_feature = torch.max(global_feature, dim=1)[0] # B 1024

    learned_coarse = self.coarse_pred(global_feature).reshape(bs, -1, 3)

    fps_count = (
        self.num_query
        if self.query_selection == 'fps_only'
        else self.num_query // 2
    )
    coarse_inp = misc.fps(xyz, fps_count)
    mem = self.mem_link(x)
    coarse_candidates = None
    query_ranking = None
    selected_query_indices = None
    rim_aux = scqr_aux

    if self.query_selection == 'ranking':
        coarse_candidates = torch.cat([learned_coarse, coarse_inp], dim=1)
        query_ranking = self.query_ranking(coarse_candidates) # b n 1
        idx = torch.argsort(query_ranking, dim=1, descending=True) # b n 1
        selected_query_indices = idx[:, :self.num_query]
        coarse = torch.gather(
            coarse_candidates,
            1,
            idx[:, :self.num_query].expand(-1, -1, coarse_candidates.size(-1))
        )
    elif self.query_selection == 'fps_preserve':
        # Keep every input FPS anchor so the coarse queries retain global
        # coverage. The remaining half are differentiable learned queries.
        learned_count = self.num_query - coarse_inp.size(1)
        coarse = torch.cat([learned_coarse[:, :learned_count], coarse_inp], dim=1)
    elif self.query_selection == 'fps_only':
        coarse = coarse_inp
    elif self.rim_query_enabled:
        rim_logits = self.rim_score_head(proxy_features).squeeze(-1)
        selected_rim_indices = diversified_topk_indices(
            rim_logits,
            coor,
            selected_count=self.rim_query_count,
            pool_size=self.rim_query_pool_size,
        )
        rim_coarse = gather_points(coor, selected_rim_indices)
        learned_count = self.num_query - self.rim_query_count
        coarse = torch.cat(
            [learned_coarse[:, :learned_count], rim_coarse], dim=1
        )
        rim_aux = {
            'proxy_coordinates': coor,
            'rim_logits': rim_logits,
            'selected_proxy_indices': selected_rim_indices,
            'selected_proxy_coordinates': rim_coarse,
        }
    else:
        # Implant prediction should not anchor query points on the defective
        # skull surface; all coarse queries are generated from global context.
        coarse = learned_coarse[:, :self.num_query]

    coarse, self._scq_last_info = self.scq(coor, mem, global_feature, coarse)

    if self.training and self.use_denoise:
        # add denoise task
        # first pick some point : 64?
        picked_points = misc.fps(xyz, 64)
        picked_points = misc.jitter_points(picked_points)
        coarse = torch.cat([coarse, picked_points], dim=1) # B 256+64 3?
        denoise_length = 64     

        # produce query
        q = self.mlp_query(
        torch.cat([
            global_feature.unsqueeze(1).expand(-1, coarse.size(1), -1),
            coarse], dim = -1)) # b n c
        if scqr_aux is not None:
            q = self._condition_scqr_queries(q, x, pe, scqr_aux, epoch)
        query_pre_decoder = q

        # forward decoder
        if self.full_instrumentation_enabled:
            q, decoder_layers = self.decoder(
                q=q, v=mem, q_pos=coarse, v_pos=coor,
                denoise_length=denoise_length,
                return_instrumentation=True,
            )
        else:
            q = self.decoder(q=q, v=mem, q_pos=coarse, v_pos=coor, denoise_length=denoise_length)
            decoder_layers = None

        if self.full_instrumentation_enabled:
            self._last_full_instrumentation = {
                'input_xyz': xyz.detach(),
                'encoder_coordinates': coor.detach(),
                'encoder_pre_adapter': encoder_pre_adapter.detach(),
                'encoder_post_adapter': encoder_post_adapter.detach(),
                'encoder_post_scqr': encoder_post_scqr.detach(),
                'encoder_memory': mem.detach(),
                'global_feature': global_feature.detach(),
                'learned_coarse': learned_coarse.detach(),
                'fps_coarse': coarse_inp.detach(),
                'coarse_candidates': None if coarse_candidates is None else coarse_candidates.detach(),
                'query_ranking': None if query_ranking is None else query_ranking.detach(),
                'selected_query_indices': None if selected_query_indices is None else selected_query_indices.detach(),
                'rim_logits': (
                    None if rim_aux is None or 'rim_logits' not in rim_aux
                    else rim_aux['rim_logits'].detach()
                ),
                'selected_rim_indices': (
                    None
                    if rim_aux is None or 'selected_proxy_indices' not in rim_aux
                    else rim_aux['selected_proxy_indices'].detach()
                ),
                'scqr_contact_logits': (
                    None if scqr_aux is None
                    else scqr_aux['contact_logits'].detach()
                ),
                'scqr_contact_probability': (
                    None if scqr_aux is None
                    else scqr_aux['contact_probability'].detach()
                ),
                'scqr_query_attention': (
                    None if scqr_aux is None
                    else scqr_aux.get('query_attention')
                ),
                'coarse': coarse.detach(),
                'query_pre_decoder': query_pre_decoder.detach(),
                'query_post_decoder': q.detach(),
                'decoder_layers': decoder_layers,
            }

        return q, coarse, denoise_length, rim_aux

    else:
        # produce query
        q = self.mlp_query(
        torch.cat([
            global_feature.unsqueeze(1).expand(-1, coarse.size(1), -1),
            coarse], dim = -1)) # b n c
        if scqr_aux is not None:
            q = self._condition_scqr_queries(q, x, pe, scqr_aux, epoch)
        query_pre_decoder = q

        # forward decoder
        if self.full_instrumentation_enabled:
            q, decoder_layers = self.decoder(
                q=q, v=mem, q_pos=coarse, v_pos=coor,
                return_instrumentation=True,
            )
        else:
            q = self.decoder(q=q, v=mem, q_pos=coarse, v_pos=coor)
            decoder_layers = None

        if self.full_instrumentation_enabled:
            self._last_full_instrumentation = {
                'input_xyz': xyz.detach(),
                'encoder_coordinates': coor.detach(),
                'encoder_pre_adapter': encoder_pre_adapter.detach(),
                'encoder_post_adapter': encoder_post_adapter.detach(),
                'encoder_post_scqr': encoder_post_scqr.detach(),
                'encoder_memory': mem.detach(),
                'global_feature': global_feature.detach(),
                'learned_coarse': learned_coarse.detach(),
                'fps_coarse': coarse_inp.detach(),
                'coarse_candidates': None if coarse_candidates is None else coarse_candidates.detach(),
                'query_ranking': None if query_ranking is None else query_ranking.detach(),
                'selected_query_indices': None if selected_query_indices is None else selected_query_indices.detach(),
                'rim_logits': (
                    None if rim_aux is None or 'rim_logits' not in rim_aux
                    else rim_aux['rim_logits'].detach()
                ),
                'selected_rim_indices': (
                    None
                    if rim_aux is None or 'selected_proxy_indices' not in rim_aux
                    else rim_aux['selected_proxy_indices'].detach()
                ),
                'scqr_contact_logits': (
                    None if scqr_aux is None
                    else scqr_aux['contact_logits'].detach()
                ),
                'scqr_contact_probability': (
                    None if scqr_aux is None
                    else scqr_aux['contact_probability'].detach()
                ),
                'scqr_query_attention': (
                    None if scqr_aux is None
                    else scqr_aux.get('query_attention')
                ),
                'coarse': coarse.detach(),
                'query_pre_decoder': query_pre_decoder.detach(),
                'query_post_decoder': q.detach(),
                'decoder_layers': decoder_layers,
            }

        return q, coarse, 0, rim_aux
