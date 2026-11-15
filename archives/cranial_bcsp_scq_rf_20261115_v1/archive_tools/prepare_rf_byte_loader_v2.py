"""Revise only RF initialization loading; never generate initialization or run tests."""
from pathlib import Path
import ast,hashlib,json

R=Path(__file__).resolve().parent.parent
M=R/'outputs/scq_rf_implementation_20261114_v1'
O=R/'outputs/scq_rf_initialization_loader_20261114_v2';O.mkdir()
old=M/'bcsp_scq_rf_residual_v1.py'
assert hashlib.sha256(old.read_bytes()).hexdigest()=='e8d00efd6b7b40edf599972d75cf98f5e9f0fa725fd969256d2f3b2329f925ef'
src=old.read_text(encoding='utf-8')
start=src.index('def load_initialization(record):')
end=src.index('\n\nclass RFResidual',start)
new='''def load_initialization(record):
    """Frozen little-endian FP32 bytes are authoritative; seed is provenance only."""
    import sys
    require(sys.byteorder == 'little', 'RF initialization byte order')
    require(tuple(SHAPES.items()) == (('V1.weight', (128, 1802)), ('V1.bias', (128,)),
                                     ('V2.weight', (3, 128)), ('V2.bias', (3,))), 'RF fixed layout')
    raw = Path(record['path']).read_bytes()
    require(len(raw) == record['bytes'] == 231171 * 4, 'RF initialization size')
    require(hashlib.sha256(raw).hexdigest() == record['sha256'], 'RF initialization SHA256')
    flat = torch.frombuffer(bytearray(raw), dtype=torch.float32)
    values, offset = {}, 0
    for name, shape in SHAPES.items():
        count = math.prod(shape)
        values[name] = flat[offset:offset + count].reshape(shape).clone()
        offset += count
    require(offset == flat.numel() and all(t.dtype == torch.float32 and t.device.type == 'cpu'
                                          and tuple(t.shape) == SHAPES[k] for k, t in values.items()), 'RF decoded structure')
    require(all(bool(torch.isfinite(x).all()) for x in values.values()), 'RF initialization finite')
    require(bool((values['V2.weight'] == 0).all()) and bool((values['V2.bias'] == 0).all()), 'RF zero output')
    return values
'''
src=src[:start]+new+src[end:]
target=O/'bcsp_scq_rf_residual_v2.py'
compile(src,str(target),'exec')
oldtree,newtree=ast.parse(old.read_text(encoding='utf-8')),ast.parse(src)
def strip(tree):return ast.dump(ast.Module([n for n in tree.body if not isinstance(n,ast.FunctionDef) or n.name!='load_initialization'],[]),include_attributes=False)
assert strip(oldtree)==strip(newtree)
loader=next(n for n in newtree.body if isinstance(n,ast.FunctionDef) and n.name=='load_initialization')
assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='initialization_values' for n in ast.walk(loader))
with target.open('x',encoding='utf-8',newline='\n') as f:f.write(src)
def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
ip3=json.loads((M/'P3_implementation_v2.json').read_bytes())
preserved=ip3['candidate_sources']+ip3['initialization']
for row in preserved:assert rec(Path(row['path']))==row
review=dict(status='RF_BYTE_LOADER_V2_STATIC_PASS_NOT_CPU_EXECUTED',new_source=rec(target),prior_source=rec(old),preserved=preserved,
    checks=dict(syntax=True,only_load_initialization_AST_changed=True,no_runtime_seed_regeneration=True,
                frozen_bytes_not_modified_or_regenerated=True,FP32_layout_byte_order_finite_zero_output_guard_retained=True,
                forward_descriptor_factory_and_initialization_generator_unchanged=True),CPU_tests=0,server_operations=0,CUDA_calls=0)
with (O/'static_review_v2.json').open('x',encoding='utf-8') as f:json.dump(review,f,indent=2)
print(json.dumps(dict(status=review['status'],source_SHA256=rec(target)['sha256'])))
