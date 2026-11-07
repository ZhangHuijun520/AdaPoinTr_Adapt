"""Capture the actual coarse head input/output, stop before FPS/query/decoder."""
def capture_prefix(torch,model,partial):
    if model.training or any(m.training for m in model.modules()):raise ValueError('eval required')
    if tuple(partial.shape)!=(1,8192,3) or partial.dtype!=torch.float32 or not bool(torch.isfinite(partial).all()):raise ValueError('partial contract')
    head=model.base_model.coarse_pred
    if head._forward_hooks or head._forward_pre_hooks:raise ValueError('existing coarse hooks rejected')
    class Captured(BaseException):pass
    saved={};handles=[]
    def before(module,args):
        if len(args)!=1 or tuple(args[0].shape)!=(1,1024):raise ValueError('actual pooled feature shape')
        z=args[0]
        if z.dtype!=torch.float32 or not bool(torch.isfinite(z).all()):raise ValueError('feature dtype/finite')
        saved['feature1024']=z.detach().clone()
    def after(module,args,out):
        if tuple(out.shape)!=(1,768) or out.dtype!=torch.float32 or not bool(torch.isfinite(out).all()):raise ValueError('actual coarse output shape/dtype/finite')
        saved['coarse']=out.detach().clone().reshape(1,256,3)
        raise Captured()
    try:
        handles.append(head.register_forward_pre_hook(before));handles.append(head.register_forward_hook(after))
        with torch.inference_mode():
            try:model(partial)
            except Captured:pass
            else:raise ValueError('coarse exit was not reached')
        if set(saved)!={'feature1024','coarse'}:raise ValueError('incomplete capture')
        return saved
    finally:
        for h in handles:h.remove()
