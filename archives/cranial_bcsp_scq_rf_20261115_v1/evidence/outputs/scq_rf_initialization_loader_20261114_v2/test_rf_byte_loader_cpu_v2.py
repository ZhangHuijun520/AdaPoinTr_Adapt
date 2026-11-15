"""One artificial CPU loader batch; read frozen bytes, never regenerate random initialization."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys,traceback
import torch
from torch import nn

O=Path(__file__).resolve().parent;R=O.parents[1]
M=R/'outputs/scq_rf_implementation_20261114_v1'
OUT=O/'cpu_loader_batch_v2'


def rec(p):return dict(path=str(p.resolve()),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())


def main():
    OUT.mkdir();(OUT/'ARTIFICIAL_FIXTURES').mkdir();checks=[];regeneration_calls=[]
    def check(name,value=True):
        assert bool(value),name
        checks.append(name)
    def reject(name,fn,expected):
        try:fn()
        except ValueError as exc:
            assert expected in str(exc),(name,str(exc));checks.append(name);return
        raise AssertionError('unexpected accept '+name)
    def fixture(name,raw):
        p=OUT/'ARTIFICIAL_FIXTURES'/name
        with p.open('xb') as f:f.write(raw)
        return rec(p)
    def digest_values(values):return {k:hashlib.sha256(v.detach().cpu().contiguous().numpy().tobytes()).hexdigest() for k,v in values.items()}
    try:
        torch.set_num_threads(2)
        static=json.loads((O/'static_review_v2.json').read_bytes())
        for row in [static['new_source'],static['prior_source'],*static['preserved']]:assert rec(Path(row['path']))==row
        check('frozen old sources factory and initialization unchanged')
        p=O/'bcsp_scq_rf_residual_v2.py'
        spec=importlib.util.spec_from_file_location('bcsp_scq_rf_residual_v1',p)
        module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
        def no_regeneration():
            regeneration_calls.append('CALLED');raise AssertionError('runtime seed regeneration forbidden')
        module.initialization_values=no_regeneration
        record=rec(M/'initialization_v1.bin');raw=Path(record['path']).read_bytes()
        manifest=json.loads((M/'initialization_manifest_v1.json').read_bytes())
        rng=torch.random.get_rng_state().clone();values=module.load_initialization(record)
        check('frozen SHA256 remains authoritative',record['sha256']=='a4024fbdb49feb41c609ae1171f04c2cb14ab794fc3663855d81395c6a1ea79e')
        check('loading makes no regeneration call',regeneration_calls==[])
        check('loading preserves common CPU RNG',torch.equal(rng,torch.random.get_rng_state()))
        check('exact four parameter names shapes FP32 CPU',tuple(values)==tuple(module.SHAPES) and all(tuple(v.shape)==module.SHAPES[k] and v.dtype==torch.float32 and v.device.type=='cpu' for k,v in values.items()))
        chunks=digest_values(values)
        check('all four loaded tensor hashes equal frozen manifest',chunks=={r['name']:r['sha256'] for r in manifest['layout']})
        check('all tensors finite and output layer zero',all(torch.isfinite(v).all() for v in values.values()) and torch.count_nonzero(values['V2.weight'])==torch.count_nonzero(values['V2.bias'])==0)
        again=module.load_initialization(record)
        check('repeated loads equal with independent storage',all(torch.equal(values[k],again[k]) and values[k].data_ptr()!=again[k].data_ptr() for k in values))
        original_hash=rec(M/'initialization_v1.bin')['sha256'];values['V1.weight'][0,0]+=1
        check('mutating returned clone does not modify frozen file',rec(M/'initialization_v1.bin')['sha256']==original_hash and digest_values(module.load_initialization(record))==chunks)
        saved_seed=module.SEED
        try:
            module.SEED=-123
            check('generation seed is provenance not loading condition',digest_values(module.load_initialization(record))==chunks and regeneration_calls==[])
        finally:module.SEED=saved_seed
        dtype=torch.get_default_dtype()
        try:
            torch.set_default_dtype(torch.float64)
            check('explicit FP32 decoding independent of default dtype',all(v.dtype==torch.float32 for v in module.load_initialization(record).values()))
        finally:torch.set_default_dtype(dtype)
        version=torch.__version__
        try:
            torch.__version__='ARTIFICIAL_DIFFERENT_VERSION_LABEL'
            check('version label does not regenerate or reject same bytes',digest_values(module.load_initialization(record))==chunks)
        finally:torch.__version__=version
        reject('wrong expected SHA256 rejected',lambda:module.load_initialization({**record,'sha256':'0'*64}),'RF initialization SHA256')
        reject('wrong declared bytes rejected',lambda:module.load_initialization({**record,'bytes':record['bytes']+4}),'RF initialization size')
        corrupt=bytearray(raw);corrupt[0]^=1;r=fixture('one_corrupt_byte.bin',corrupt)
        reject('one byte corruption rejected by frozen hash',lambda:module.load_initialization({**r,'sha256':record['sha256']}),'RF initialization SHA256')
        for name,data in [('truncated.bin',raw[:-4]),('extra_element.bin',raw+bytes(4)),('empty.bin',b''),('float64_sized.bin',raw+raw)]:
            r=fixture(name,data)
            reject('invalid total layout bytes rejected '+name,lambda:module.load_initialization(r),'RF initialization size')
        for name,bits in [('NaN',struct.pack('<f',float('nan'))),('Infinity',struct.pack('<f',float('inf')))]:
            r=fixture(name+'.bin',bits+raw[4:])
            reject('nonfinite rejected even with matching file hash '+name,lambda:module.load_initialization(r),'RF initialization finite')
        offset=(128*1802+128)*4
        nonzero=bytearray(raw);nonzero[offset:offset+4]=struct.pack('<f',1.)
        r=fixture('nonzero_V2_weight.bin',nonzero)
        reject('nonzero V2 weight rejected with matching file hash',lambda:module.load_initialization(r),'RF zero output')
        nonzero=bytearray(raw);nonzero[-4:]=struct.pack('<f',1.)
        r=fixture('nonzero_V2_bias.bin',nonzero)
        reject('nonzero V2 bias rejected with matching file hash',lambda:module.load_initialization(r),'RF zero output')
        saved_shapes=module.SHAPES
        try:
            module.SHAPES={**saved_shapes,'V1.weight':(1802,128)}
            reject('wrong fixed shape rejected',lambda:module.load_initialization(record),'RF fixed layout')
            module.SHAPES=dict(reversed(list(saved_shapes.items())))
            reject('wrong serialized parameter order rejected',lambda:module.load_initialization(record),'RF fixed layout')
        finally:module.SHAPES=saved_shapes
        endian=sys.byteorder
        try:
            sys.byteorder='big'
            reject('unsupported host byte order rejected',lambda:module.load_initialization(record),'RF initialization byte order')
        finally:sys.byteorder=endian
        check('negative fixtures preserve RNG and never regenerate',torch.equal(rng,torch.random.get_rng_state()) and regeneration_calls==[])
        def knn_forbidden(*args):raise AssertionError('no forward/KNN in loader tests')
        rng=torch.random.get_rng_state().clone()
        heads=[module.RFResidual(v,knn_forbidden,record) for v in ('RF-Static','RF-Requery')]
        check('actual RF head constructors use frozen bytes no regeneration',all(digest_values(h.state_dict())==chunks for h in heads) and regeneration_calls==[])
        check('head constructors preserve common RNG',torch.equal(rng,torch.random.get_rng_state()))
        check('head parameter count and persistent keys unchanged',all(sum(v.numel() for v in h.parameters())==231171 and tuple(h.state_dict())==tuple(module.SHAPES) for h in heads))
        # Exercise the unchanged factory with the new residual module under its established alias.
        S=R/'outputs/cranial_bcsp_scq_implementation_20261113_v1'
        L=R/'outputs/cranial_bcsp_fullmamba_20261110/lqi_implementation_v1'
        P=R/'outputs/cranial_bcsp_mamba_p1_20261104/minimal_implementation_v1'
        sys.path[:0]=[str(M),str(S),str(L),str(P)]
        import bcsp_scq_rf_factory_v1 as factory
        import bcsp_scq_residual_v1 as first
        first_record=json.loads((S/'initialization_manifest_v1.json').read_bytes())
        class Fixture(nn.Module):
            def __init__(self):
                super().__init__();self.base_model=nn.Module();self.base_model.decoder=nn.Identity();self.base_model.decoder.knn=knn_forbidden
                self.base_model.scq=first.SCQResidual('S',knn_forbidden,first_record)
                self.shared=nn.Parameter(torch.ones(2,2))
        models=[]
        for variant in ('RF-Static','RF-Requery'):
            model=Fixture();common=digest_values(model.state_dict());before=torch.random.get_rng_state().clone()
            model,evidence=factory.install(model,variant,record)
            check('unchanged factory binds corrected residual '+variant,isinstance(model.base_model.rf,module.RFResidual) and digest_values(model.base_model.rf.state_dict())==chunks and evidence['additional_parameters']==231171)
            check('factory preserves common state and RNG '+variant,all(digest_values(model.state_dict())[k]==v for k,v in common.items()) and torch.equal(before,torch.random.get_rng_state()))
            models.append(model)
        check('both factory variants share exact initialized state',digest_values(models[0].state_dict())==digest_values(models[1].state_dict()))
        check('all frozen bytes unchanged and zero regeneration across batch',rec(M/'initialization_v1.bin')==record and regeneration_calls==[])
        result=dict(status='RF_FROZEN_BYTE_LOADER_CPU_PASS',checks=checks,count=len(checks),source=rec(p),test=rec(Path(__file__)),
                    frozen_initialization=record,loaded_tensor_hashes=chunks,torch=torch.__version__,regeneration_calls=0,
                    forward_calls=0,loss_calls=0,backward_calls=0,optimizer_steps=0,CUDA=False,server_operations=0,
                    limitations=['Only loader, actual RF constructors and unchanged factory on artificial containers tested; no full-model forward/backward repeated.',
                                 'Artificial version-label/default-dtype checks do not emulate another actual PyTorch release or CPU architecture.',
                                 'Negative binary fixtures are synthetic copies; authoritative initialization file remains unchanged.'])
        with (OUT/'result_v2.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2,allow_nan=False)
        print(json.dumps(dict(status=result['status'],count=len(checks),regeneration_calls=0)))
    except BaseException as exc:
        with (OUT/'failure_v2.json').open('x',encoding='utf-8') as f:json.dump(dict(status='FAILED_STOP_NO_RETRY',checks=checks,error=repr(exc),traceback=traceback.format_exc()),f,indent=2)
        raise


if __name__=='__main__':main()
