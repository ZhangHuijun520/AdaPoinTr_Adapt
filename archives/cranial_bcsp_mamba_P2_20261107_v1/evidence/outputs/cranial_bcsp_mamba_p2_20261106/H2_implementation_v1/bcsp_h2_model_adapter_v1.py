"""Isolated H2 installation after the frozen M0 factory; old sources unchanged."""
import types
import torch
from bcsp_h2_range_v1 import CONTRACT,RangeHead,auxiliary,moments,soft_couple,require

def validate_baseline(model):
    b=model.base_model
    require(model.num_query==256 and model.num_points==8192 and model.factor==32 and model.decoder_type=='fc','frozen point/head contract')
    require(model.denoise_weight==0 and model.fine_coverage_weight==1 and model.fine_local_weight==0,'original losses')
    require(b.query_selection=='learned_only' and not b.use_denoise and not b.rim_query_enabled and not b.scqr_contract.enabled and b.scqr_local_geometry is None and not b.encoder_adapter.enabled,'original learned_only path')
    require(not model.scqr_contract.enabled and not model.scqr_contract.contact_supervision_enabled,'SCQR disabled')
    require(all(getattr(model,n) is False for n in ['coarse_geometry_guard_enabled','local_rim_guard_enabled','moment_trust_enabled','dense_contact_enabled','rim_query_enabled']),'H1 and other objectives disabled')
    require(not model.full_instrumentation_enabled and not b.full_instrumentation_enabled,'dedicated H2 instrumentation only')
    require(not b.coarse_pred._forward_hooks and not b.coarse_pred._forward_pre_hooks and not model._forward_pre_hooks,'no conflicting hooks')
    require(not hasattr(model,'h2_range_head') and all(p.device.type=='cpu' and p.dtype==torch.float32 for p in model.parameters()),'attach once to initialized FP32 CPU model')

class Controller:
    def __init__(self,model,mode):
        self.model=model;self.mode=mode;self.context=None;self.generation=0;self.override=None;self.original_get_loss=model.get_loss
    def begin(self,module,args):
        require(len(args)==1,'D-only positional forward interface')
        if self.context is not None and self.context['training']:
            require(self.context['consumed'],'unconsumed training forward')
        require(not self.model.training or self.override is None,'intervention forbidden in training')
        self.context=None;self.generation+=1
    def head(self,module,args,out):
        require(self.context is None and len(args)==1 and tuple(out.shape)==(args[0].shape[0],768),'one actual coarse head output')
        raw=out.reshape(-1,256,3);delta=self.model.h2_range_head(args[0]);_,radius=moments(raw)
        condition=delta if self.override is None else torch.full_like(delta,self.override)
        if self.mode=='COUPLE':used,scale,_=soft_couple(raw,condition)
        else:used=raw;scale=torch.ones_like(delta)
        self.context=dict(raw=raw,used=used,delta=delta,condition=condition,scale=scale,radius_raw=radius,generation=self.generation,training=self.model.training,consumed=False,log=None)
        return out if self.mode=='AUX' else used.reshape_as(out)
    def loss(self,ret,target,*args,**kwargs):
        c=self.context
        require(c is not None and not c['consumed'] and len(ret) in [4,5] and ret[0].shape==c['used'].shape,'one loss per current forward')
        require(ret[0].data_ptr()==c['used'].data_ptr(),'original coarse consumer/return binding')
        base=self.original_get_loss(ret,target,*args,**kwargs)
        require(isinstance(base,(tuple,list)) and len(base)==2,'original two loss values')
        raw_aux,t=auxiliary(c['delta'],c['raw'],target);weighted=.1*raw_aux
        require(base[1].ndim==0 and bool(torch.isfinite(base[1])),'finite original reconstruction')
        with torch.no_grad():
            mr,rr=moments(c['raw']);mu,ru=moments(c['used']);mp,rp=moments(ret[3]);mg,rg=moments(target)
            c['log']=dict(H2_mode=self.mode,H2_generation=c['generation'],H2_aux_raw=float(raw_aux.detach()),H2_aux_weighted=float(weighted.detach()),loss_original_reconstruction=float(base[1].detach()),loss_dense_includes_H2_aux=True,H2_delta=c['delta'].detach().flatten().tolist(),H2_target_t=t.detach().tolist(),H2_scale=c['scale'].detach().flatten().tolist(),H2_centroid_raw=mr[:,0].tolist(),H2_centroid_used=mu[:,0].tolist(),H2_centroid_dense=mp[:,0].tolist(),H2_centroid_GT=mg[:,0].tolist(),H2_radius_raw=rr.tolist(),H2_radius_used=ru.tolist(),H2_radius_dense=rp.tolist(),H2_radius_GT=rg.tolist())
        c['consumed']=True
        return base[0],base[1]+weighted
    def record(self):
        require(self.context is not None and self.context['consumed'] and self.context['log'] is not None,'log only after loss')
        return dict(self.context['log'])
    def intervention(self,value):
        require(self.mode=='COUPLE' and not self.model.training,'COUPLE eval-only intervention')
        require(value is None or (isinstance(value,(int,float)) and torch.isfinite(torch.tensor(value)).item()),'finite scalar intervention')
        self.override=None if value is None else float(value)

def install_h2(model,mode):
    require(mode in ['OFF','AUX','COUPLE'],'H2 mode')
    if mode=='OFF':return model
    validate_baseline(model)
    head=RangeHead();model.add_module('h2_range_head',head);controller=Controller(model,mode)
    model.register_forward_pre_hook(controller.begin)
    model.base_model.coarse_pred.register_forward_hook(controller.head)
    def get_loss(self,ret,target,*args,**kwargs):return controller.loss(ret,target,*args,**kwargs)
    model.get_loss=types.MethodType(get_loss,model)
    model.h2_runtime_record=controller.record
    model.h2_metadata=lambda:dict(CONTRACT,mode=mode)
    model.h2_intervention=controller.intervention
    # No duplicate model/module registration or altered common state_dict prefixes.
    object.__setattr__(model,'_h2_controller',controller)
    return model

def build_h2(parent_factory,legacy_builder,mode,seed=0):
    require(seed==0 and mode in ['OFF','AUX','COUPLE'],'fixed first H2 pair')
    model,evidence=parent_factory.build_model(legacy_builder,'M0',seed=seed)
    before={n:v.detach().clone() for n,v in model.state_dict().items()};rng=torch.get_rng_state().clone()
    install_h2(model,mode)
    require(all(torch.equal(v,model.state_dict()[n]) for n,v in before.items()) and torch.equal(rng,torch.get_rng_state()),'common initialized state/RNG changed')
    new=set(model.state_dict())-set(before)
    require(new==(set() if mode=='OFF' else {'h2_range_head.weight','h2_range_head.bias'}),'exact state delta')
    return model,dict(evidence,H2_mode=mode,H2_contract=None if mode=='OFF' else dict(CONTRACT),common_state_after_H2_unchanged=True)

def validate_checkpoint_contract(payload,mode):
    require(mode in ['AUX','COUPLE'] and payload.get('H2')==dict(CONTRACT,mode=mode),'checkpoint H2 mode/constants')
    require(payload.get('stage')=='BCSP_INPUT_DENSITY_V1' and payload.get('epoch')==99 and payload.get('updates')==3900,'fixed final checkpoint')
