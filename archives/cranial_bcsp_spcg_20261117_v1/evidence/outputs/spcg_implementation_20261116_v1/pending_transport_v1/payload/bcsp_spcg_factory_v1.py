"""Isolated single-expression replacement of the bound real PCTransformer.forward."""
import ast
import hashlib
from pathlib import Path
import types
import torch
from bcsp_spcg_head_v1 import SPCGHead, need

ORIGINAL = 'self.coarse_pred(global_feature).reshape(bs, -1, 3)'
REPLACEMENT = 'self.spcg_head(xyz, coor, x, global_feature)'

def replacement_forward(original_forward, source, expected_sha):
    raw = Path(source).read_bytes()
    need(hashlib.sha256(raw).hexdigest()==expected_sha,'bound mother source')
    tree = ast.parse(raw)
    cls = next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='PCTransformer')
    method = next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='forward')
    needle = ast.dump(ast.parse(ORIGINAL,mode='eval').body,include_attributes=False)
    before = ast.dump(method,include_attributes=False)
    class Replace(ast.NodeTransformer):
        count = 0
        def visit_Assign(self, n):
            if any(isinstance(t,ast.Name) and t.id=='learned_coarse' for t in n.targets):
                need(ast.dump(n.value,include_attributes=False)==needle,'exact coarse expression')
                self.count += 1
                n.value = ast.copy_location(ast.parse(REPLACEMENT,mode='eval').body,n.value)
            return n
    transform=Replace();method=transform.visit(method);need(transform.count==1,'exact one coarse assignment')
    method.decorator_list=[]
    module=ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[]))
    env=dict(original_forward.__func__.__globals__)
    exec(compile(module,str(source)+'::SPCG_one_expression','exec'),env)
    return env['forward'],dict(replaced_assignments=1,before_ast_sha256=hashlib.sha256(before.encode()).hexdigest(),after_ast_sha256=hashlib.sha256(ast.dump(method,include_attributes=False).encode()).hexdigest())

def install(model, arm, U, initialization, source, source_sha):
    need(arm in ('G0','G1','G2'),'arm')
    base=model.base_model
    need(base.query_selection=='learned_only' and not base.use_denoise,'unchanged learned-only no denoise')
    need(isinstance(base.mem_link,torch.nn.Identity),'Memory identity width')
    need(getattr(base,'scqr_local_geometry',None) is None and getattr(base,'scqr_query_conditioner',None) is None,'SCQR disabled')
    need(not getattr(model,'coarse_geometry_guard_enabled',False) and not hasattr(model,'h2_head'),'H1/H2 disabled')
    need(not any(hasattr(base,k) for k in ('h0','h1','rf_head','spcg_head')),'no feedback or prior SPCG')
    evidence=dict(arm=arm,source_sha256=source_sha,old_head_removed=False,artificial_fixture=bool(model.f0_evidence['artificial_fixture']))
    if arm=='G0':return model,evidence
    before={n:p.detach().clone() for n,p in model.state_dict().items() if not n.startswith('base_model.coarse_pred.')}
    method,patch=replacement_forward(base.forward,source,source_sha)
    head=SPCGHead(arm,U,initialization)
    del base.coarse_pred
    base.add_module('spcg_head',head)
    base.forward=types.MethodType(method,base)
    need(all(torch.equal(p,model.state_dict()[n]) for n,p in before.items()),'common state unchanged')
    need(not any(n.startswith('base_model.coarse_pred.') for n,_ in model.named_parameters()),'old head remains')
    evidence.update(old_head_removed=True,patch=patch,head_parameters=sum(p.numel() for p in head.parameters()),additional_parameters=8963)
    model.spcg_evidence=evidence
    return model,evidence

def build_model(legacy_builder, lqi_factory, arm, U, initialization, source, source_sha):
    model, parent=lqi_factory.build_model(legacy_builder,seed=0)
    model,evidence=install(model,arm,U,initialization,source,source_sha)
    return model,dict(parent=parent,**evidence)
