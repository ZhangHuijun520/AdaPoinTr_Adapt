import sys,types,json,importlib.util
from pathlib import Path
import numpy as np
N=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('trace_capture',N/'trace_capture_v1.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
class T:
 def __init__(self,a):self.a=np.asarray(a)
 def detach(self):return self
 def cpu(self):return self
 def numpy(self):return self.a
mod=types.ModuleType('artificial_trace_model');sys.modules[mod.__name__]=mod
mod.pointnet2_utils=types.SimpleNamespace(furthest_point_sample=lambda xyz,n:T(np.arange(n)[None]))
mod.knn_point=lambda k,keys,query:T(np.zeros((1,2,k),np.int64))
class DGCNN_Grouper:
 @staticmethod
 def fps_downsample(c,x,n):mod.pointnet2_utils.furthest_point_sample(c,n);return c,x
 def get_graph_feature(self,cq,xq,ck,xk):mod.knn_point(16,ck,cq);return xq
DGCNN_Grouper.__module__=mod.__name__;group=DGCNN_Grouper()
class Model:
 def modules(self):return [group]
baseline=(DGCNN_Grouper.__dict__['fps_downsample'],DGCNN_Grouper.get_graph_feature,mod.knn_point,mod.pointnet2_utils.furthest_point_sample)
t=T(np.arange(6).reshape(1,3,2));original=t.a.copy();checks=[]
with m.TraceCapture(Model()) as cap:
 for n in [512,256]:assert group.fps_downsample(t,t,n)[0] is t
 for _ in range(4):assert group.get_graph_feature(t,t,t,t) is t
 checks+=['original FPS result identity','original graph result identity','two FPS/four graph calls']
assert len(cap.arrays)==18;checks+=['18 exact captured arrays']
assert np.array_equal(t.a,original);checks+=['input unchanged']
assert baseline==(DGCNN_Grouper.__dict__['fps_downsample'],DGCNN_Grouper.get_graph_feature,mod.knn_point,mod.pointnet2_utils.furthest_point_sample);checks+=['all functions restored']
t.a[:]=0;assert np.array_equal(cap.arrays['fps512_input_coordinates'],original);checks+=['captured arrays independent copies']
try:
 with m.TraceCapture(Model()):raise ValueError('fixture')
except ValueError:pass
assert baseline==(DGCNN_Grouper.__dict__['fps_downsample'],DGCNN_Grouper.get_graph_feature,mod.knn_point,mod.pointnet2_utils.furthest_point_sample);checks+=['restored on exception']
try:
 with m.TraceCapture(Model()):pass
except RuntimeError:checks+=['incomplete trace rejected']
assert len(checks)==9
out={'passed':checks,'count':len(checks),'scope':'artificial in-memory function interception only; no torch/model/CUDA; not GPU equivalence'}
with (N/'CPU_trace_contract_v1.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(out))
