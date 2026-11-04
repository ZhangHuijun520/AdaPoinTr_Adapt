"""Observe grouper FPS/KNN calls, return original tensors, always restore patches."""
import sys

class TraceCapture:
    def __init__(self, model):
        groups=[m for m in model.modules() if type(m).__name__=='DGCNN_Grouper']
        if len(groups)!=1:raise RuntimeError('exactly one DGCNN_Grouper required')
        self.cls=type(groups[0]);self.mod=sys.modules[self.cls.__module__]
        self.provider=self.mod.pointnet2_utils;self.arrays={};self.fps_active=False;self.graph_active=False;self.fps_count=0;self.graph_count=0
    def copy(self,key,tensor):
        if key in self.arrays:raise RuntimeError('duplicate trace key '+key)
        self.arrays[key]=tensor.detach().cpu().numpy().copy()
    def __enter__(self):
        cls=self.cls;self.old_static=cls.__dict__['fps_downsample'];self.old_fps=cls.fps_downsample;self.old_graph=cls.get_graph_feature;self.old_knn=self.mod.knn_point;self.old_provider=self.provider.furthest_point_sample
        def fps(coor,x,count):
            if count not in (512,256) or self.fps_active:raise RuntimeError('unexpected grouper FPS')
            self.fps_count+=1;self.fps_active=True;self.copy('fps%d_input_coordinates'%count,coor)
            try:
                result=self.old_fps(coor,x,count)
                self.copy('fps%d_output_coordinates'%count,result[0]);return result
            finally:self.fps_active=False
        def provider(xyz,count):
            result=self.old_provider(xyz,count)
            if self.fps_active:self.copy('fps%d_indices'%count,result)
            return result
        def graph(instance,cq,xq,ck,xk):
            self.graph_count+=1;stage=self.graph_count
            if stage>4 or self.graph_active:raise RuntimeError('unexpected graph call')
            self.copy('graph%d_query_coordinates'%stage,cq);self.copy('graph%d_key_coordinates'%stage,ck);self.graph_active=True
            try:return self.old_graph(instance,cq,xq,ck,xk)
            finally:self.graph_active=False
        def knn(k,keys,query):
            result=self.old_knn(k,keys,query)
            if self.graph_active:self.copy('graph%d_knn_indices'%self.graph_count,result)
            return result
        cls.fps_downsample=staticmethod(fps);cls.get_graph_feature=graph;self.mod.knn_point=knn;self.provider.furthest_point_sample=provider
        return self
    def __exit__(self,kind,value,tb):
        self.cls.fps_downsample=self.old_static;self.cls.get_graph_feature=self.old_graph;self.mod.knn_point=self.old_knn;self.provider.furthest_point_sample=self.old_provider
        if kind is None and (self.fps_count!=2 or self.graph_count!=4 or len(self.arrays)!=18):raise RuntimeError('exact two FPS/four KNN trace contract')
        return False
