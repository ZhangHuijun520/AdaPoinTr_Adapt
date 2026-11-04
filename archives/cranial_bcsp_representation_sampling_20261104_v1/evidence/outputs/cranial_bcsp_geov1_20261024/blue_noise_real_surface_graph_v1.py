"""Six open cases, frozen pools, voxel-surface graph path sampling; CPU only.
All graph edges are paths on original faces. Not exact continuous geodesics.
"""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2')
from pathlib import Path
B=Path(__file__).resolve().parent;OLD=B/'blue_noise_pilot_20261103_v1';O=B/'blue_noise_real_surface_graph_20261103_v1'
import csv,gc,hashlib,heapq,importlib.util,json,sys,time,traceback
import numpy as np
import psutil
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra,connected_components

START=time.monotonic();PEAK=0;N=8192;M=32768
SCOPE=B.parent/'cranial_geometry_diagnostic_20261023/raw_pairing_v1/scope.json'
sp=importlib.util.spec_from_file_location('original_readonly_surface',B/'real_data_qc_v1.py');sb=importlib.util.module_from_spec(sp);sp.loader.exec_module(sb)
def guard():
    global PEAK
    PEAK=max(PEAK,psutil.Process().memory_info().rss)
    if time.monotonic()-START>1800 or PEAK>6*1024**3:raise RuntimeError('30min / monitored6GiB budget')
sb.guard=guard
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for v in iter(lambda:f.read(1048576),b''):h.update(v)
    return h.hexdigest()
def dump(p,x):
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False)
def npz(p,**x):
    with p.open('xb') as f:np.savez_compressed(f,**x)

def surface_graph(s,A,o,shape):
    """Shared-edge dual graph plus valid face-corner routes via a common face.
    Ambiguous four-incidence edges blocked; no vertex-only links between fans.
    """
    x,_=sb.face_geometry(s,A,o);F=len(x);a=s[1].astype(int);b=(a+1)%3;c=(a+2)%3
    center=2*s[0].astype(np.int64);center[np.arange(F),a]+=s[2]
    coords=np.repeat(center,4,axis=0);shift=np.c_[b,b,c,c].ravel();sign=np.tile([-1,1,-1,1],F)
    coords[np.arange(4*F),shift]+=sign
    edge_axis=np.c_[c,c,b,b].ravel()
    keys=np.ravel_multi_index((edge_axis,coords[:,0]+1,coords[:,1]+1,coords[:,2]+1),(3,*(2*np.array(shape)+1)))
    order=np.argsort(keys);starts=np.r_[0,np.flatnonzero(np.diff(keys[order]))+1];counts=np.diff(np.r_[starts,len(order)])
    if not np.isin(counts,[2,4]).all():raise ValueError('unexpected exposed-face edge incidence')
    valid=starts[counts==2];left=order[valid];right=order[valid+1]
    f=left//4;g=right//4;nb=np.full((F,4),-1,np.int32);nb[f,left%4]=g;nb[g,right%4]=f
    midpoint=(coords[left]/2)@A+o
    weight=np.linalg.norm(x[f]-midpoint,axis=1)+np.linalg.norm(x[g]-midpoint,axis=1)
    src=[f];dst=[g];val=[weight]
    del keys,order,coords,edge_axis,shift,sign,midpoint,left,right;guard()
    for ib,ic in [(0,2),(0,3),(1,2),(1,3)]:
        tag=(nb[:,ib]>=0)&(nb[:,ic]>=0);central=np.flatnonzero(tag);u=nb[tag,ib];v=nb[tag,ic]
        corner=center[central].copy();corner[np.arange(len(central)),b[central]]+=-1 if ib==0 else 1
        corner[np.arange(len(central)),c[central]]+=-1 if ic==2 else 1
        point=(corner/2)@A+o
        src.append(u);dst.append(v);val.append(np.linalg.norm(x[u]-point,axis=1)+np.linalg.norm(x[v]-point,axis=1))
    # Multiple valid paths may connect same centers; choose minimum, never sum lengths.
    src=np.concatenate(src);dst=np.concatenate(dst);length=np.concatenate(val)
    low=np.minimum(src,dst).astype(np.int64);high=np.maximum(src,dst).astype(np.int64)
    edgekey=low*F+high;ix=np.argsort(edgekey);st=np.r_[0,np.flatnonzero(np.diff(edgekey[ix]))+1]
    u=low[ix[st]];v=high[ix[st]];length=np.minimum.reduceat(length[ix],st)
    graph=coo_matrix((np.r_[length,length],(np.r_[u,v],np.r_[v,u])),shape=(F,F)).tocsr()
    assert np.all(length+1e-9>=np.linalg.norm(x[u]-x[v],axis=1))
    components=connected_components(graph,directed=False,return_labels=False)
    info={'faces':F,'undirected_path_edges':len(length),'blocked_ambiguous_original_edges':int((counts==4).sum()),'components':int(components),
      'path_definition':'shared edge midpoint; or shared corner via an intervening face with two valid edge links',
      'approximation':'8-neighbor-like planar stencil, conservative endpoint-center paths; not continuous exact geodesic'}
    return graph,nb,x,info

def checks():
    A=np.eye(3);o=np.zeros(3);mask=np.ones((9,9,3),bool);s=sb.surface(mask);g,nb,x,info=surface_graph(s,A,o,mask.shape)
    def fid(q):return int(np.flatnonzero((s[0]==q).all(1)&(s[1]==2)&(s[2]==1))[0])
    a=fid([2,2,2]);b=fid([5,3,2]);d=float(dijkstra(g,indices=a,limit=10)[b]);ratio=d/np.sqrt(10)
    assert 1<=ratio<1.083
    # Edge-touch cubes: the ambiguous common edge must not join surface fans.
    m=np.zeros((4,4,4),bool);m[1,1,1]=True;m[2,2,1]=True
    ss=sb.surface(m);gg,_,_,ii=surface_graph(ss,A,o,m.shape)
    assert ii['blocked_ambiguous_original_edges']==1 and ii['components']==2
    m=np.zeros((4,4,4),bool);m[1,1,1]=True;m[2,2,2]=True
    _,_,_,ii=surface_graph(sb.surface(m),A,o,m.shape);assert ii['components']==2
    assert (nb>=0).all() and info['components']==1
    return {'status':'PASS','planar_center_distance_mm':d,'planar_exact_distance_mm':float(np.sqrt(10)),
      'planar_center_relative_excess':ratio-1,'checks':['closed box manifold adjacency','valid path length >= chord',
      'planar stencil calibration','four-face edge blocked','vertex-touch fans not joined'],
      'limit':'calibration does not bound all curved-surface or point-endpoint errors'}

def bounded_paths(p,face_ids,pairs,graph,nb,x,s,A,o,R,spacing):
    """Tile-local Dijkstra; any center-path <=R fits in source tile plus R.
    Endpoint-to-center paths have extra discretization error. Same-face and
    adjacent-face distances use direct or exact unfolded local paths.
    """
    F=len(x);a,b=pairs.T;order=np.argsort(a,kind='stable');aa=a[order];bb=b[order]
    out=np.full(len(pairs),np.inf);offset=np.linalg.norm(p-x[face_ids],axis=1)
    local=((x-o)@np.linalg.inv(A))*spacing;pc=local[face_ids]
    origin=pc.min(0);tiles=np.floor((pc-origin)/R).astype(int);tilekeys,tile_id=np.unique(tiles,axis=0,return_inverse=True)
    tree=cKDTree(local);margin=2*float(spacing.max());active_sources=np.unique(a)
    processed=0
    for ti,key in enumerate(tilekeys):
        sources=active_sources[tile_id[active_sources]==ti]
        if not len(sources):continue
        lo=origin+key*R-R-margin;hi=origin+(key+1)*R+R+margin
        center=(lo+hi)/2;ids=np.array(tree.query_ball_point(center,float(np.linalg.norm((hi-lo)/2))),dtype=np.int64)
        ids=np.sort(ids[np.all((local[ids]>=lo)&(local[ids]<=hi),axis=1)])
        if len(ids)>150000:raise RuntimeError('local Dijkstra graph exceeds150k faces')
        sub=graph[ids][:,ids]
        for start in range(0,len(sources),16):
            batch=sources[start:start+16];srcfaces,back=np.unique(face_ids[batch],return_inverse=True)
            src_local=np.searchsorted(ids,srcfaces);assert np.array_equal(ids[src_local],srcfaces)
            distances=dijkstra(sub,directed=False,indices=src_local,limit=R)
            for k,point in enumerate(batch):
                left,right=np.searchsorted(aa,[point,point+1]);target=bb[left:right];targets=face_ids[target]
                loc=np.searchsorted(ids,targets)
                assert (loc<len(ids)).all() and np.array_equal(ids[loc],targets)
                out[order[left:right]]=distances[back[k],loc]+offset[point]+offset[target]
            guard()
        processed+=len(sources)
        if ti%100==0:print('  PATH_TILES',ti+1,'/',len(tilekeys),'sources',processed,flush=True)
    de=np.linalg.norm(p[a]-p[b],axis=1);same=face_ids[a]==face_ids[b];out[same]=de[same]
    adjacent=nb[face_ids[a]]==face_ids[b,None];tag=adjacent.any(1);indices=np.flatnonzero(tag)
    if len(indices):
        slot=adjacent[tag].argmax(1);fa=face_ids[a[tag]];axis=s[1][fa].astype(int);other=np.where(slot<2,(axis+1)%3,(axis+2)%3)
        sign=np.where(slot%2==0,-1,1);mid=x[fa]+sign[:,None]*A[other]/2
        along=np.where(slot<2,(axis+2)%3,(axis+1)%3);unit=A[along]/spacing[along,None]
        v1=p[a[tag]]-mid;v2=p[b[tag]]-mid;t1=(v1*unit).sum(1);t2=(v2*unit).sum(1)
        h1=np.sqrt(np.maximum(0,(v1*v1).sum(1)-t1*t1));h2=np.sqrt(np.maximum(0,(v2*v2).sum(1)-t2*t2))
        unfolded=np.sqrt((h1+h2)**2+(t1-t2)**2);out[indices]=np.minimum(out[indices],unfolded)
    out=np.maximum(out,de)
    info={'pairs':len(pairs),'within_graph_radius':int((out<R).sum()),'same_face_exact_pairs':int(same.sum()),
      'adjacent_face_unfolded_pairs':int(tag.sum()),'tiles':len(tilekeys),
      'median_ratio_graph_to_Euclidean_for_retained_pairs':float(np.median(out[out<R]/de[out<R]))}
    return out,info

def eliminate(pairs,length,npoints,R):
    a,b=pairs.T;w=np.maximum(0,1-length/R)**8;tag=w>0;a=a[tag];b=b[tag];w=w[tag]
    graph=coo_matrix((np.r_[w,w],(np.r_[a,b],np.r_[b,a])),shape=(npoints,npoints)).tocsr()
    score=np.asarray(graph.sum(1)).ravel();live=np.ones(npoints,bool);version=np.zeros(npoints,np.int64)
    heap=[(-float(v),i,0) for i,v in enumerate(score)];heapq.heapify(heap)
    for step in range(npoints-N):
        while True:
            _,i,v=heapq.heappop(heap)
            if live[i] and version[i]==v:break
        live[i]=False;lo,hi=graph.indptr[i:i+2];js=graph.indices[lo:hi];weight=graph.data[lo:hi];tag=live[js];js=js[tag];weight=weight[tag]
        score[js]-=weight;version[js]+=1
        for j in js:heapq.heappush(heap,(-float(score[j]),int(j),int(version[j])))
        if step%1024==0:
            guard()
            if len(heap)>8*npoints:heap=[(-float(score[j]),int(j),int(version[j])) for j in np.flatnonzero(live)];heapq.heapify(heap)
    return np.flatnonzero(live)

def metric(ref,w,p):
    d=cKDTree(p).query(ref,workers=2)[0];order=np.argsort(d);cw=np.cumsum(w[order])
    return {'cover_0_5mm':float(np.average(d<=.5,weights=w)),'cover_1mm':float(np.average(d<=1,weights=w)),
      'cover_2mm':float(np.average(d<=2,weights=w)),'p95_mm':float(d[order[np.searchsorted(cw,.95*cw[-1])]])}

def main():
    if O.exists():raise RuntimeError('new result directory only')
    old_protocol=json.loads((OLD/'protocol.json').read_text());oldmetrics=json.loads((OLD/'metrics.json').read_text())
    cases=json.loads(SCOPE.read_text(encoding='utf-8'))['cases'];assert len(cases)==6
    bindings={str(Path(__file__)):sha(Path(__file__)),str(SCOPE):sha(SCOPE)}
    for path in [B/'blue_noise_pilot_v1.py',B/'real_data_qc_v1.py',sb.READER,sb.LOCK]:
        assert sha(path)==old_protocol['source_hashes'][str(path)];bindings[str(path)]=sha(path)
    for c in cases:
        for role in ['defective','implant']:
            p=c['raw_paths'][role];assert sha(Path(p))==old_protocol['source_hashes'][p];bindings[p]=sha(Path(p))
    oldmanifest=json.loads((OLD/'contents.json').read_text())
    for name,x in oldmanifest.items():
        if name.startswith('samples/') and not name.startswith('samples/phantom') or name in ['metrics.json','protocol.json']:
            assert sha(OLD/name)==x['sha256'];bindings[str(OLD/name)]=x['sha256']
    O.mkdir();(O/'samples').mkdir()
    dump(O/'protocol.json',{'status':'FROZEN_BEFORE_CPU_CHECKS','source_hashes':bindings,'N':N,'pool_size':M,'seeds':[0,1,2],
      'cases':[c['dataset']+'_'+c['case_id'] for c in cases],'candidate':'surface-graph path-distance kernel sample elimination',
      'representation':'unchanged original exposed voxel quads, no smoothing/marching cubes',
      'adjacency':'shared whole edge with exactly two incident faces; four-face edges blocked and counted; no bare point-touch jumps',
      'graph_paths':'face centers via shared edge midpoint; optional face-corner paths via common face with valid edge adjacency',
      'endpoint_paths':'point-center offsets plus shortest dual-graph path; same face direct; adjacent face unfolded exact',
      'distance_warning':'conservative graph approximation, not continuous exact geodesic; directional and endpoint discretization bias',
      'pool_recovery':'original unchanged area sampler + seed; byte-identical prefix and historic Euclidean selected subset required before new selection',
      'kernel':'max(0,1-d/R)^8; same frozen R=2sqrt(area/N); no radius/weight tuning',
      'target_policy':'G decoded and J derived only after graph-selected indices persisted; original target untouched',
      'evaluation':'same exact exposed-face-center area-weighted references; J/E cover .5/1/2mm, same-region and unrestricted',
      'limits':{'seconds':1800,'monitored_RSS_GiB':6,'max_local_graph_faces':150000,'max_undirected_pool_pairs':8000000},
      'prohibitions':['no new data or holdout','no model/GPU/server/training','no anatomical inner/outer claims without labels','no automatic tuning']})
    dump(O/'checks.json',checks());print('CHECKS_PASS',flush=True);rows=[];geometry=[]
    for c in cases:
        cid=c['dataset']+'_'+c['case_id'];begin=time.monotonic();print('BEGIN',cid,flush=True)
        D,A,o=sb.raw.read_mask(Path(c['raw_paths']['defective']));spacing=np.linalg.norm(A,axis=1)
        assert np.max(np.abs((A/spacing[:,None])@(A/spacing[:,None]).T-np.eye(3)))<1e-8
        s=sb.surface(D);graph,nb,x,info=surface_graph(s,A,o,D.shape);print('GRAPH',cid,info,flush=True)
        _,w=sb.face_geometry(s,A,o);R=2*np.sqrt(w.sum()/N);selected_sets=[];pathinfo=[]
        for seed in [0,1,2]:
            p,faceids,_,_=sb.sample(s,A,o,seed,M)
            with np.load(OLD/'samples'/f'{cid}_seed{seed}_V1_common_pool.npz',allow_pickle=False) as z:assert np.array_equal(p[:N],z['xyz'])
            with np.load(OLD/'samples'/f'{cid}_seed{seed}_Euclidean_elimination.npz',allow_pickle=False) as z:
                oldidx=z['pool_indices'];assert np.array_equal(p[oldidx],z['xyz'])
            tree=cKDTree(p);count=(int(tree.count_neighbors(tree,R))-M)//2
            if count>8000000:raise RuntimeError('8M pool pair bound')
            pairs=tree.query_pairs(R,output_type='ndarray')
            print('PATH_BEGIN',cid,seed,'pairs',len(pairs),flush=True)
            lengths,pi=bounded_paths(p,faceids,pairs,graph,nb,x,s,A,o,R,spacing)
            selected=eliminate(pairs,lengths,M,R);assert len(selected)==N
            npz(O/'samples'/f'{cid}_seed{seed}_surface_graph.npz',xyz=p[selected],pool_indices=selected,face_ids=faceids[selected])
            selected_sets.append((seed,p,faceids,oldidx,selected));pathinfo.append({'seed':seed,**pi})
            print('SELECTED',cid,seed,pi,flush=True);del pairs,lengths;gc.collect();guard()
        G,F,f=sb.raw.read_mask(Path(c['raw_paths']['implant']));assert np.array_equal(A,F) and np.array_equal(o,f) and not (D&G).any()
        J=sb.contact(s,G)
        for seed,p,faceids,oldidx,newidx in selected_sets:
            for method,idx in [('V1_common_pool',np.arange(N)),('Euclidean_elimination',oldidx),('surface_graph',newidx)]:
                row={'case':cid,'seed':seed,'method':method,'count':N,'regions':{}}
                for name,tag in [('J',J),('E',~J)]:
                    same=tag[faceids[idx]];assert same.any()
                    row['regions'][name]={'point_count':int(same.sum()),'unrestricted':metric(x[tag],w[tag],p[idx]),
                      'same_region':metric(x[tag],w[tag],p[idx[same]])}
                if method!='surface_graph':
                    old=next(r for r in oldmetrics if r['case']==cid and r['seed']==seed and r['method']==method)
                    for region in ['J','E']:
                        assert row['regions'][region]['point_count']==old['regions'][region]['point_count']
                        for metricname,value in row['regions'][region]['unrestricted'].items():assert abs(value-old['regions'][region]['unrestricted'][metricname])<1e-10
                rows.append(row)
        gi={'case':cid,'R':float(R),**info,'path_diagnostics':pathinfo,'seconds':time.monotonic()-begin}
        geometry.append(gi);dump(O/f'{cid}_geometry.json',gi);dump(O/f'{cid}_metrics.json',rows[-9:])
        print('CASE_DONE',cid,round(time.monotonic()-begin,1),flush=True)
        del D,G,s,graph,nb,x,selected_sets;gc.collect();guard()
    assert len(rows)==54 and all(sha(Path(p))==h for p,h in bindings.items())
    dump(O/'metrics.json',rows);dump(O/'summary.json',{'status':'COMPLETED_REAL_SURFACE_GRAPH_CPU_ONLY','rows':54,'cases':6,'seeds':3,
      'geometry':geometry,'source_hashes_unchanged':True,'recovered_pools_match_saved_bytes':True,'historic_reference_metrics_reproduced':True,
      'seconds':time.monotonic()-START,'checkpoint_peak_RSS_bytes':PEAK,'GPU_model_server_calls':0})
    dump(O/'contents.json',{str(p.relative_to(O)):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(O.rglob('*')) if p.is_file()})
    print('COMPLETED',flush=True)

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    try:main()
    except BaseException as e:
        if O.exists() and not (O/'failure.json').exists():dump(O/'failure.json',{'status':'FAILED_STOP','error':repr(e),'traceback':traceback.format_exc()})
        traceback.print_exc();raise
