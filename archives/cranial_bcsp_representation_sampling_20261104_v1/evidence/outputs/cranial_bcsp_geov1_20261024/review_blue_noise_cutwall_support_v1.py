"""Saved-point cutwall attribution only: no RNG, sampling or elimination calls."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2',MPLBACKEND='Agg')
from pathlib import Path
B=Path(__file__).resolve().parent;P=B/'blue_noise_pilot_20261103_v1';O=P/'cutwall_support_review_v2'
os.environ['MPLCONFIGDIR']=str(P/'cutwall_support_review_plot_cache_v1')
import csv,gc,hashlib,importlib.util,json,sys,time,traceback
import numpy as np
import psutil
from scipy.spatial import cKDTree
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

START=time.monotonic();PEAK=0
SCOPE=B.parent/'cranial_geometry_diagnostic_20261023/raw_pairing_v1/scope.json'
spec=importlib.util.spec_from_file_location('read_only_existing_surface',B/'real_data_qc_v1.py')
sb=importlib.util.module_from_spec(spec);spec.loader.exec_module(sb)

def guard():
    global PEAK
    PEAK=max(PEAK,psutil.Process().memory_info().rss)
    if time.monotonic()-START>900 or PEAK>6*1024**3:raise RuntimeError('15min / monitored6GiB bound')
sb.guard=guard

def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def dump(p,x):
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False)

def writecsv(p,rows):
    with p.open('x',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def key(c,a,shape):
    return np.ravel_multi_index((a,c[:,0]+1,c[:,1]+1,c[:,2]+1),(3,*(2*np.array(shape)+1)))

def face_map(p,A,o,s,shape):
    """Exact voxel-face membership, not nearest-face-center classification."""
    v=(p-o)@np.linalg.inv(A)
    err=np.abs(v-(np.floor(v)+.5));a=err.argmin(1)
    assert np.max(err[np.arange(len(p)),a])<1e-7
    c=2*np.rint(v).astype(np.int64);c[np.arange(len(p)),a]=np.rint(2*v[np.arange(len(p)),a]).astype(np.int64)
    sc=2*s[0].astype(np.int64);sc[np.arange(len(sc)),s[1]]+=s[2]
    sk=key(sc,s[1],shape);order=np.argsort(sk);pk=key(c,a,shape)
    loc=np.searchsorted(sk[order],pk);assert (loc<len(sk)).all() and np.array_equal(sk[order[loc]],pk)
    ids=order[loc];local=v-s[0][ids]
    assert np.abs(local).max()<=.5+1e-7
    return ids

def nearest(p,labels,ref):
    out={}
    for name,tag in [('J',labels==1),('E',labels==0)]:
        ix=np.flatnonzero(tag);assert len(ix)
        d,i=cKDTree(p[ix]).query(ref,workers=2);out['d'+name]=d;out['i'+name]=ix[i]
    return out

def frac(tag,w):return float(np.average(tag,weights=w))

def kernel_attribution(p,labels,baseline,base_labels,base_ids,candidate_ids,R,normals):
    jids=np.flatnonzero(base_labels==1);tree=cKDTree(p);nb=tree.query_ball_point(baseline[jids],R,workers=2)
    kept=np.isin(base_ids[jids],candidate_ids);index_to_candidate={int(v):i for i,v in enumerate(candidate_ids)}
    result=[]
    for k,(bi,js) in enumerate(zip(jids,nb)):
        js=np.array(js,dtype=int)
        if kept[k]:js=js[js!=index_to_candidate[int(base_ids[bi])]]
        dist=np.linalg.norm(p[js]-baseline[bi],axis=1);ww=np.maximum(0,1-dist/R)**8
        e=labels[js]==0;sw=ww.sum();eshare=float(ww[e].sum()/sw) if sw>0 else None
        if e.any():
            ej=js[e][np.argmin(dist[e])];ed=float(np.linalg.norm(p[ej]-baseline[bi]));dot=float(normals['baseline'][bi]@normals['candidate'][ej])
        else:ed=None;dot=None
        result.append({'kept':bool(kept[k]),'E_weight_share':eshare,'E_weight_positive':bool((ww[e]>0).any()),
          'nearest_E_within_R_mm':ed,'nearest_E_normal_dot':dot})
    out={}
    for status in [False,True]:
        rr=[r for r in result if r['kept']==status]
        valid=[r['E_weight_share'] for r in rr if r['E_weight_share'] is not None]
        out['retained' if status else 'removed']={'baseline_J_points':len(rr),
          'fraction_with_positive_surviving_E_kernel':float(np.mean([r['E_weight_positive'] for r in rr])) if rr else None,
          'mean_surviving_E_kernel_share':float(np.mean(valid)) if valid else None,
          'fraction_E_normal_near_orthogonal':float(np.mean([abs(r['nearest_E_normal_dot'])<.5 for r in rr if r['nearest_E_normal_dot'] is not None])) if any(r['nearest_E_normal_dot'] is not None for r in rr) else None}
    return out

def plot_patch(cid,seed_data,D,G,s,J,A,o,spacing,chosen,patch_ids,jref,jlocal,R):
    face_ids=np.flatnonzero(J)[patch_ids==chosen]
    center=jlocal[patch_ids==chosen].mean(0);qc=s[0][face_ids]
    anchor=qc[np.argmin(np.linalg.norm(qc*spacing-center,axis=1))]
    axes=s[1][face_ids];normal_axis=int(np.bincount(axes,minlength=3).argmax())
    others=[a for a in range(3) if a!=normal_axis]
    tangent=max(others,key=lambda a:float(np.var(qc[:,a]*spacing[a])))
    third=next(a for a in others if a!=tangent);u,v=tangent,normal_axis
    lo=np.maximum(0,np.floor(anchor-1.25*R/spacing).astype(int));hi=np.minimum(D.shape,np.ceil(anchor+1.25*R/spacing).astype(int)+1)
    indices=np.meshgrid(np.arange(lo[u],hi[u]),np.arange(lo[v],hi[v]),indexing='ij')
    ijk=[np.full(indices[0].shape,int(anchor[a])) for a in range(3)];ijk[u]=indices[0];ijk[v]=indices[1]
    image=np.zeros(indices[0].shape,int);image[D[tuple(ijk)]]=1;image[G[tuple(ijk)]]=2
    extent=[(lo[u]-.5)*spacing[u],(hi[u]-.5)*spacing[u],(lo[v]-.5)*spacing[v],(hi[v]-.5)*spacing[v]]
    fig,axs=plt.subplots(3,2,figsize=(10,11),layout='constrained')
    display_counts=[]
    for seed,data in enumerate(seed_data):
        for col,name in enumerate(['V1_common_pool','Euclidean_elimination']):
            ax=axs[seed,col];ax.imshow(image.T,origin='lower',extent=extent,cmap=ListedColormap(['#ffffff','#bbbbbb','#e3d5ec']),vmin=0,vmax=2)
            p=data[name]['p'];lab=data[name]['labels'];local=((p-o)@np.linalg.inv(A))*spacing
            show=(np.abs(local[:,third]-anchor[third]*spacing[third])<=1.5*spacing[third])
            show&=(local[:,u]>=extent[0])&(local[:,u]<=extent[1])&(local[:,v]>=extent[2])&(local[:,v]<=extent[3])
            for label,color,caption in [(0,'#E69F00','other surface E'),(1,'#0072B2','cut wall J')]:
                ix=show&(lab==label);ax.scatter(local[ix,u],local[ix,v],s=16,c=color,label=caption,alpha=.85)
            if name=='V1_common_pool':
                lost=show&(lab==1)&~np.isin(data[name]['pool_ids'],data['Euclidean_elimination']['pool_ids'])
                ax.scatter(local[lost,u],local[lost,v],s=26,marker='x',c='#cc3311',label='V1 J absent from candidate')
            ax.set_xlim(extent[:2]);ax.set_ylim(extent[2:]);ax.set_aspect('equal')
            ax.set_title(f'{name}; seed {seed}; J={int((show&(lab==1)).sum())}, E={int((show&(lab==0)).sum())}',fontsize=9)
            ax.set_xlabel(f'native axis {u} (mm)');ax.set_ylabel(f'native axis {v} (mm)')
            if seed==0:ax.legend(fontsize=6,loc='upper right')
            display_counts.append({'seed':seed,'method':name,'J':int((show&(lab==1)).sum()),'E':int((show&(lab==0)).sum())})
    fig.suptitle(f'{cid}: largest mean cut-wall count-loss tile\nGray=D, purple=G; fixed voxel slice, points within +/-1.5 voxels; no registration',fontsize=10)
    fig.savefig(O/'figures'/f'{cid}_worst_count_tile.png',dpi=150);plt.close(fig)
    return {'native_voxel_anchor':anchor.tolist(),'display_plane_axes':[u,v],'fixed_axis':third,'display_slab_halfwidth_mm':float(1.5*spacing[third]),
      'world_anchor_mm':(anchor@A+o).tolist(),'display_counts':display_counts,'note':'Points projected through 3-voxel-thick slab onto center binary slice; projection is not exact surface contact proof'}

def main():
    if O.exists():raise RuntimeError('new output only')
    protocol=json.loads((P/'protocol.json').read_text());metrics=json.loads((P/'metrics.json').read_text())
    frozen=json.loads((P/'contents.json').read_text())
    assert all((P/k).stat().st_size==v['bytes'] and sha(P/k)==v['sha256'] for k,v in frozen.items())
    scope=json.loads(SCOPE.read_text(encoding='utf-8'));cases=scope['cases']
    assert len(cases)==6
    bindings={str(P/k):v['sha256'] for k,v in frozen.items()}
    bindings.update({str(Path(__file__)):sha(Path(__file__)),str(SCOPE):sha(SCOPE)})
    for c in cases:
        for role in ['defective','implant']:
            p=c['raw_paths'][role];h=sha(p);assert h==protocol['source_hashes'][p];bindings[p]=h
    O.mkdir();(O/'figures').mkdir()
    dump(O/'protocol.json',{'status':'FROZEN_BEFORE_DIAGNOSTICS','source_hashes':bindings,'cases':[c['dataset']+'_'+c['case_id'] for c in cases],
      'seeds':[0,1,2],'input':'existing xyz, pool_indices and labels only; raw D/G re-read solely for exact face references and section context',
      'no_resampling':True,'thresholds_mm':[.5,1,2],
      'spatial_tiles':'native physical axes; side equal original frozen kernel R; origin=min J face-center local coordinate; all tiles included',
      'plot_selection':'for each of three SkullBreak cases, tile with largest mean J point-count decrease across three seeds, one fixed 3-voxel-slab display; not a new performance subset',
      'cross_surface_evidence':'J/E kernel interaction with saved survivors, not elimination-time causal reconstruction; no anatomical inner/outer labels',
      'limits':{'seconds':900,'monitored_RSS_GiB':6},'prohibitions':['no RNG/pool regeneration','no eliminate calls','no parameter change','no model/GPU/server']})
    allrows=[];alltiles=[];details=[]
    for c in cases:
        guard();cid=c['dataset']+'_'+c['case_id'];print('BEGIN',cid,flush=True)
        D,A,o=sb.raw.read_mask(Path(c['raw_paths']['defective']));G,F,f=sb.raw.read_mask(Path(c['raw_paths']['implant']))
        assert D.shape==G.shape and np.array_equal(A,F) and np.array_equal(o,f) and not (D&G).any()
        spacing=np.linalg.norm(A,axis=1);assert np.max(np.abs((A/spacing[:,None])@(A/spacing[:,None]).T-np.eye(3)))<1e-8
        s=sb.surface(D);x,w=sb.face_geometry(s,A,o);J=sb.contact(s,G);assert J.any()
        ref=x[J];jw=w[J];jlocal=((ref-o)@np.linalg.inv(A))*spacing
        R=next(r['kernel']['radius_mm'] for r in metrics if r['case']==cid)
        xyz_tiles=np.floor((jlocal-jlocal.min(0))/R).astype(int);tile_keys,patch_ids=np.unique(xyz_tiles,axis=0,return_inverse=True)
        K=len(tile_keys);area=np.bincount(patch_ids,weights=jw,minlength=K)
        seed_data=[];kernel=[];tiles_per_seed=[]
        for seed in [0,1,2]:
            data={}
            for name in ['V1_common_pool','Euclidean_elimination']:
                with np.load(P/'samples'/f'{cid}_seed{seed}_{name}.npz',allow_pickle=False) as z:
                    p=z['xyz'];lab=z['region_labels'];pool_ids=z['pool_indices']
                ids=face_map(p,A,o,s,D.shape);assert np.array_equal(J[ids].astype(int),lab)
                normal=np.linalg.inv(A)[:,s[1][ids]].T*s[2][ids,None];normal/=np.linalg.norm(normal,axis=1)[:,None]
                n=nearest(p,lab,ref)
                jcoord=((p[lab==1]-o)@np.linalg.inv(A))*spacing
                pc=np.floor((jcoord-jlocal.min(0))/R).astype(int)
                # Face-center tile defines membership, avoiding within-face jitter at cell borders.
                face_j_local=((x[ids[lab==1]]-o)@np.linalg.inv(A))*spacing
                pc=np.floor((face_j_local-jlocal.min(0))/R).astype(int)
                lookup={tuple(v):i for i,v in enumerate(tile_keys)}
                counts=np.bincount([lookup[tuple(v)] for v in pc],minlength=K)
                data[name]={'p':p,'labels':lab,'pool_ids':pool_ids,'normals':normal,'nearest':n,'counts':counts}
                old=next(r for r in metrics if r['case']==cid and r['seed']==seed and r['method']==name)
                assert int((lab==1).sum())==old['regions']['J']['point_count']
                row={'case':cid,'seed':seed,'method':name,'J_point_count':int((lab==1).sum()),'radius_mm':R}
                for t in [.5,1,2]:
                    keyt=str(t);dj,de=n['dJ'],n['dE']
                    row['J_cover_'+keyt]=frac(dj<=t,jw)
                    row['E_only_rescue_'+keyt]=frac((dj>t)&(de<=t),jw)
                    row['uncovered_'+keyt]=frac((dj>t)&(de>t),jw)
                    row['nearest_is_E_'+keyt]=frac((de<dj)&(de<=t),jw)
                    metric_key={.5:'cover_0_5mm',1:'cover_1mm',2:'cover_2mm'}[t]
                    assert abs(row['J_cover_'+keyt]-old['regions']['J']['same_surface'][metric_key])<1e-10
                    assert abs(row['J_cover_'+keyt]+row['E_only_rescue_'+keyt]-old['regions']['J']['unrestricted'][metric_key])<1e-10
                allrows.append(row)
            a,b=data['V1_common_pool'],data['Euclidean_elimination']
            pos={int(i):k for k,i in enumerate(b['pool_ids'])}
            shared=[(i,pos[int(pid)]) for i,pid in enumerate(a['pool_ids']) if int(pid) in pos]
            assert all(np.array_equal(a['p'][i],b['p'][j]) for i,j in shared)
            attribution=kernel_attribution(b['p'],b['labels'],a['p'],a['labels'],a['pool_ids'],b['pool_ids'],R,{'baseline':a['normals'],'candidate':b['normals']})
            kernel.append({'seed':seed,**attribution})
            tile={'delta_count':b['counts']-a['counts']}
            for t in [.5,1,2]:
                va=a['nearest']['dJ']<=t;vb=b['nearest']['dJ']<=t
                lost=va&~vb;gained=~va&vb
                tile['lost_'+str(t)]=np.bincount(patch_ids,weights=jw*lost,minlength=K)
                tile['gained_'+str(t)]=np.bincount(patch_ids,weights=jw*gained,minlength=K)
                tile['lost_E_rescue_'+str(t)]=np.bincount(patch_ids,weights=jw*(lost&(b['nearest']['dE']<=t)),minlength=K)
            tiles_per_seed.append(tile);seed_data.append(data)
        tile_rows=[]
        for i,v in enumerate(tile_keys):
            row={'case':cid,'tile_x':int(v[0]),'tile_y':int(v[1]),'tile_z':int(v[2]),'J_area_mm2':float(area[i]),
              'world_center_x_mm':float(((jlocal.min(0)+(v+.5)*R)/spacing@A+o)[0]),
              'world_center_y_mm':float(((jlocal.min(0)+(v+.5)*R)/spacing@A+o)[1]),
              'world_center_z_mm':float(((jlocal.min(0)+(v+.5)*R)/spacing@A+o)[2]),
              'mean_J_count_delta':float(np.mean([t['delta_count'][i] for t in tiles_per_seed]))}
            for threshold in [.5,1,2]:
                for kind in ['lost','gained','lost_E_rescue']:
                    row[kind+'_area_mm2_'+str(threshold)]=float(np.mean([t[kind+'_'+str(threshold)][i] for t in tiles_per_seed]))
            tile_rows.append(row)
        chosen=int(np.argmin([r['mean_J_count_delta'] for r in tile_rows]));alltiles+=tile_rows
        case_detail={'case':cid,'J_reference_faces':len(ref),'J_area_mm2':float(jw.sum()),'tile_count':K,'survivor_kernel_attribution':kernel,
          'worst_count_tile':tile_rows[chosen]}
        if cid.startswith('SkullBreak'):
            case_detail['section']=plot_patch(cid,seed_data,D,G,s,J,A,o,spacing,chosen,patch_ids,ref,jlocal,R)
        # Local reference field: all J faces, no worst-case subset removal.
        np.savez_compressed(O/f'{cid}_J_support_fields.npz',xyz=ref,area=jw,tile_ids=patch_ids,
          V1_dJ=np.stack([d['V1_common_pool']['nearest']['dJ'] for d in seed_data]),
          candidate_dJ=np.stack([d['Euclidean_elimination']['nearest']['dJ'] for d in seed_data]),
          V1_dE=np.stack([d['V1_common_pool']['nearest']['dE'] for d in seed_data]),
          candidate_dE=np.stack([d['Euclidean_elimination']['nearest']['dE'] for d in seed_data]))
        details.append(case_detail);dump(O/f'{cid}_detail.json',case_detail)
        print('DONE',cid,flush=True);del D,G,s,x,seed_data;gc.collect();guard()
    writecsv(O/'support_attribution.csv',allrows);writecsv(O/'all_spatial_tiles.csv',alltiles)
    assert len(allrows)==36 and all(sha(p)==h for p,h in bindings.items())
    dump(O/'summary.json',{'status':'COMPLETED_SAVED_POINT_DIAGNOSTIC','rows':allrows,'details':details,
      'seconds':time.monotonic()-START,'checkpoint_peak_RSS_bytes':PEAK,'frozen_inputs_unchanged':True,
      'no_resampling_or_elimination':True,'no_model_GPU_server_calls':True,'exact_saved_point_face_mapping_and_original_coverage_reproduction':True})
    dump(O/'contents.json',{str(p.relative_to(O)):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(O.rglob('*')) if p.is_file() and 'mpl_cache' not in p.parts})
    print('COMPLETED',flush=True)

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    try:main()
    except BaseException as e:
        if O.exists() and not (O/'failure.json').exists():dump(O/'failure.json',{'error':repr(e),'traceback':traceback.format_exc(),'status':'FAILED_STOP_NO_RETRY'})
        traceback.print_exc();raise
