"""Six-case, local CPU analysis of user-specified masks and hash-matched clouds.

No model import, no data regeneration, no source writes, no server access.
Voxel-face center quadrature is explicitly NOT a smooth anatomical mesh.
"""
import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
import csv
import gc
import gzip
import hashlib
import json
import re
import sys
import time
from pathlib import Path
import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree
from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parent
OUT = BASE / 'raw_pairing_v1'
OLD = BASE / 'result_v2'
STRUCT = ndimage.generate_binary_structure(3, 1)

def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''):
            h.update(b)
    return h.hexdigest()

def dump(p, obj):
    with p.open('x', encoding='utf-8') as f:
        json.dump(obj, f, indent=2, ensure_ascii=False, allow_nan=False)

def header(p):
    with p.open('rb') as f:
        assert f.readline().startswith(b'NRRD000')
        lines = []
        for _ in range(100):
            s = f.readline()
            if s.strip() == b'':
                break
            lines.append(s.decode('ascii').strip())
        else:
            raise ValueError('Header too long')
        offset = f.tell()
    fields = dict(s.split(':', 1) for s in lines if s and not s.startswith('#') and ':' in s)
    fields = {k: v.strip() for k,v in fields.items()}
    assert fields['dimension'] == '3' and fields['encoding'] == 'gzip'
    assert 'data file' not in fields and 'byte skip' not in fields and 'line skip' not in fields
    types = {'int32':'i4', 'uint8':'u1'}
    dt = np.dtype(types[fields['type']]).newbyteorder('<' if fields.get('endian', 'little') == 'little' else '>')
    shape = tuple(map(int, fields['sizes'].split()))
    assert len(shape) == 3 and np.prod(shape) <= 160_000_000
    vectors = re.findall(r'\(([^)]+)\)', fields['space directions'])
    directions = np.array([[float(x) for x in v.split(',')] for v in vectors])
    origin = np.array([float(x) for x in fields.get('space origin', '(0,0,0)').strip('()').split(',')])
    assert directions.shape == (3,3) and origin.shape == (3,) and abs(np.linalg.det(directions)) > 1e-9
    return fields, offset, dt, shape, directions, origin

def read_mask(p):
    fields, offset, dt, shape, directions, origin = header(p)
    with p.open('rb') as f:
        f.seek(offset)
        with gzip.GzipFile(fileobj=f) as z:
            raw = z.read(int(np.prod(shape))*dt.itemsize + 1)
    assert len(raw) == int(np.prod(shape))*dt.itemsize
    volume = np.frombuffer(raw, dtype=dt).reshape(shape, order='F')
    assert np.isfinite(volume).all()
    mask = np.asarray(volume > .5, order='C')
    return mask, directions, origin

def mask_hash(mask):
    h = hashlib.sha256(np.asarray(mask.shape, dtype=np.int32).tobytes())
    a = mask.ravel(order='C')
    for s in range(0, len(a), 8*1024*1024):
        h.update(np.packbits(a[s:s+8*1024*1024]).tobytes())
    return h.hexdigest()

def shifted_neighbor(mask, axis, sign):
    a = [slice(None)]*3
    b = [slice(None)]*3
    a[axis] = slice(None,-1) if sign == 1 else slice(1,None)
    b[axis] = slice(1,None) if sign == 1 else slice(None,-1)
    return tuple(a), tuple(b)

def faces(d, g, axis, sign):
    a,b = shifted_neighbor(d,axis,sign)
    exposed = d.copy()
    exposed[a] &= ~d[b]
    coords = np.argwhere(exposed)
    del exposed
    neighbor = coords.copy()
    neighbor[:,axis] += sign
    inside = (neighbor[:,axis] >= 0) & (neighbor[:,axis] < d.shape[axis])
    contact = np.zeros(len(coords), dtype=bool)
    contact[inside] = g[tuple(neighbor[inside].T)]
    return coords, contact

def describe(x):
    if not len(x):
        return None
    return {k:float(v) for k,v in zip(['median','p95','max','mean'], [*np.percentile(x,[50,95,100]),np.mean(x)])}

def face_coverage(world, tree):
    distances = np.empty(len(world), dtype=float)
    for s in range(0,len(world),200000):
        distances[s:s+200000] = tree.query(world[s:s+200000],workers=1)[0]
    return distances

def checks():
    d = np.zeros((3,3,3), dtype=bool)
    g = d.copy()
    d[1,1,1] = True
    assert sum(len(faces(d,g,a,s)[0]) for a in range(3) for s in [-1,1]) == 6
    g[2,1,1] = True
    assert sum(int(faces(d,g,a,s)[1].sum()) for a in range(3) for s in [-1,1]) == 1
    dirs = np.array([[.4,0,0],[0,.5,0],[0,0,.7]])
    idx = np.array([[1.,2.,3.]])
    assert np.allclose((idx @ dirs) @ np.linalg.inv(dirs), idx)
    assert np.isclose(np.linalg.norm(np.cross(dirs[1],dirs[2])), .35)
    assert len(np.unique(np.array([[0,0],[0,0],[1,1]]),axis=0)) == 2
    return 5

def picture(ds, cid, d, g, wall, pindex, directions):
    font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 22)
    small = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 17)
    im = Image.new('RGB',(1800,1160),'white')
    dr = ImageDraw.Draw(im)
    dr.text((20,10),f'{ds} {cid}: raw binary mask sections + existing input points',fill='black',font=font)
    dr.text((20,43),'Blue=residual bone; orange=missing bone; magenta=cut-adjacent bone voxels; black=sampled input',fill='black',font=small)
    dr.text((20,68),'No interpolation or re-sampling of source data. Bottom: defect ROI, point slab +/-1 mm.',fill='black',font=small)
    wc = np.argwhere(wall)
    center = np.median(wc, axis=0).astype(int)
    spacing = np.linalg.norm(directions,axis=1)
    gram = directions @ directions.T
    assert np.allclose(gram, np.diag(np.diag(gram)),atol=1e-6), 'Oblique nonorthogonal planes require explicit reslicing'
    for col,(u,v,w) in enumerate([(0,1,2),(0,2,1),(1,2,0)]):
        idx = int(center[w])
        sl = [slice(None)]*3
        sl[w] = idx
        rem = [a for a in range(3) if a != w]
        def orient(a):
            return a[tuple(sl)].transpose([rem.index(v),rem.index(u)])
        dd,gg,ww = orient(d),orient(g),orient(wall)
        rgb = np.full((*dd.shape,3),255,dtype=np.uint8)
        rgb[dd] = [145,198,224]
        rgb[gg] = [235,165,116]
        rgb[ww] = [204,70,150]
        for row in range(2):
            if row == 0:
                x0,y0,x1,y1 = 0,0,d.shape[u],d.shape[v]
            else:
                x0 = max(0,int(wc[:,u].min()-8/spacing[u]))
                x1 = min(d.shape[u],int(wc[:,u].max()+8/spacing[u])+1)
                y0 = max(0,int(wc[:,v].min()-8/spacing[v]))
                y1 = min(d.shape[v],int(wc[:,v].max()+8/spacing[v])+1)
            phys_w,phys_h = (x1-x0)*spacing[u],(y1-y0)*spacing[v]
            factor = min(550/phys_w,425/phys_h)
            size = (max(1,round(phys_w*factor)),max(1,round(phys_h*factor)))
            tile = Image.fromarray(rgb[y0:y1,x0:x1]).resize(size,Image.Resampling.NEAREST)
            left = col*600+25
            top = 160+row*490
            im.paste(tile,(left,top))
            dr.rectangle((left,top,left+size[0],top+size[1]),outline='black')
            dr.text((left,top-45),f'Voxel axes {u}/{v}; slice {w}={idx}; '+('full' if row==0 else 'ROI'),fill='black',font=small)
            dr.text((left,top+size[1]+5),f'{phys_w:.1f} x {phys_h:.1f} mm (equal physical aspect)',fill='black',font=small)
            if row == 1:
                sel = (np.abs(pindex[:,w]-idx)*spacing[w] <= 1.0)
                sel &= (pindex[:,u]>=x0)&(pindex[:,u]<x1)&(pindex[:,v]>=y0)&(pindex[:,v]<y1)
                for pt in pindex[sel]:
                    x = left+(pt[u]-x0+.5)*size[0]/(x1-x0)
                    y = top+(pt[v]-y0+.5)*size[1]/(y1-y0)
                    dr.ellipse((x-2,y-2,x+2,y+2),fill='black')
                dr.text((left,top-22),f'Existing input points in displayed slab/ROI: {int(sel.sum())}',fill='black',font=small)
    im.save(OUT/(ds+'_'+cid+'_raw_sections.png'))

def main():
    assert not OUT.exists(), 'Refuse overwrite'
    OUT.mkdir()
    start = time.time()
    sanity = checks()
    old = json.loads((OLD/'results.json').read_text())['cases']
    scope = json.loads((OLD/'selected_scope.json').read_text())['cases']
    plans = []
    for item in scope:
        ds = item['dataset']
        if ds not in ['SkullFix','SkullBreak']:
            continue
        rec = item['record']
        root = Path('E:/dataset/SkullFix/extracted/training_set' if ds=='SkullFix' else 'E:/dataset/SkullBreak/raw')
        pcroot = Path('E:/dataset/SkullFix/pointcloud_defective_norm' if ds=='SkullFix' else 'E:/dataset/SkullBreakPC')
        paths = {role:root/rel for role,rel in rec['raw'].items()}
        pc = pcroot/rec['point_path']
        expected = next(c['sha256_before'] for c in old if c['dataset']==ds and c['case_id']==rec['case_id'])
        assert sha(pc)==expected
        hashes = {str(p):sha(p) for p in [*paths.values(),pc]}
        plans.append({'dataset':ds,'case_id':rec['case_id'],'raw_paths':{k:str(v) for k,v in paths.items()},
                      'point_path':str(pc),'hashes_before':hashes,'record':rec})
    assert len(plans)==6
    dump(OUT/'scope.json',{'cases':plans,'read_only_sources':True,'diagnostic_tolerances_mm':[1,2],
                          'reference':'Area-weighted voxel-face-center quadrature; not continuous smooth mesh area',
                          'inner_outer_semantic_labels':'Not automatically inferred; visually inspect paired sections'})
    results=[]
    for plan in plans:
        ds,cid,rec = plan['dataset'],plan['case_id'],plan['record']
        print('READ',ds,cid,flush=True)
        masks={}
        for role,p in plan['raw_paths'].items():
            m,dirs,origin=read_mask(Path(p))
            if masks:
                assert m.shape==shape and np.allclose(dirs,directions,atol=1e-7) and np.allclose(origin,orig,atol=1e-5)
            else:
                shape,directions,orig=m.shape,dirs,origin
            masks[role]=m
        c,d,g = masks['complete'],masks['defective'],masks['implant']
        assert tuple(rec['voxel_shape'])==shape
        assert np.allclose(rec['space_directions'],directions,atol=1e-7) and np.allclose(rec['space_origin'],orig,atol=1e-5)
        assert np.array_equal(c, d|g) and not np.any(d&g), 'Raw triplet is not a disjoint partition'
        counts={k:int(v.sum()) for k,v in masks.items()}
        assert counts['complete']==rec['quality']['complete_voxels'] and counts['defective']==rec['quality']['defective_voxels'] and counts['implant']==rec['quality']['implant_voxels']
        if ds=='SkullBreak':
            assert mask_hash(c)==rec['complete_mask_sha256']
        with np.load(plan['point_path'],allow_pickle=False) as z:
            p=np.asarray(z['partial'],dtype=float)*float(z['scale'])+np.asarray(z['centroid'],dtype=float)
            target=np.asarray(z['implant'],dtype=float)*float(z['scale'])+np.asarray(z['centroid'],dtype=float)
        pidx=(p-orig)@np.linalg.inv(directions)
        pint=np.rint(pidx).astype(int)
        assert np.max(np.abs(pidx-pint))<.001 and np.all(pint>=0) and np.all(pint<np.array(shape))
        assert d[tuple(pint.T)].all()
        boundary=d & ~ndimage.binary_erosion(d,structure=STRUCT,border_value=0)
        assert boundary[tuple(pint.T)].all()
        tree=cKDTree(p)
        bc=np.argwhere(boundary)
        bdist=face_coverage(orig+bc@directions,tree)
        boundary_summary={'boundary_voxels':len(bc),'coverage_at_1mm':float(np.mean(bdist<=1)),
                          'coverage_at_2mm':float(np.mean(bdist<=2)),'distance_mm':describe(bdist)}
        del bc,bdist,boundary
        boundary_counts={}
        for role in ['complete','implant']:
            b=masks[role] & ~ndimage.binary_erosion(masks[role],structure=STRUCT,border_value=0)
            boundary_counts[role]=int(b.sum())
            del b
        wall=np.zeros_like(d)
        total_area=0.
        whole_cover=np.zeros(2)
        wall_area=0.
        wall_cover=np.zeros(2)
        wallcoords=[]
        wallweights=[]
        nfaces=0
        wallfaces=0
        for axis in range(3):
            others=[a for a in range(3) if a!=axis]
            area=float(np.linalg.norm(np.cross(directions[others[0]],directions[others[1]])))
            for sign in [-1,1]:
                coords,contact=faces(d,g,axis,sign)
                wall[tuple(coords[contact].T)]=True
                fc=coords.astype(float)
                fc[:,axis]+=sign*.5
                world=orig+fc@directions
                distances=face_coverage(world,tree)
                nfaces+=len(fc)
                total_area+=len(fc)*area
                whole_cover+=np.array([(distances<=e).sum() for e in [1,2]])*area
                wallfaces+=int(contact.sum())
                wall_area+=int(contact.sum())*area
                wall_cover+=np.array([(distances[contact]<=e).sum() for e in [1,2]])*area
                wallcoords.append(world[contact])
                wallweights.append(np.full(int(contact.sum()),area))
                del coords,fc,world,distances,contact
        assert wallfaces>0 and wall_area>0
        wworld=np.concatenate(wallcoords)
        wweights=np.concatenate(wallweights)
        sampled_wall=wall[tuple(pint.T)]
        ptowall=cKDTree(wworld).query(p,workers=1)[0]
        denseband=ptowall<=2
        sparseband=cKDTree(target).query(p,workers=1)[0]<=2
        strictcover=None
        if sampled_wall.any():
            wd=face_coverage(wworld,cKDTree(p[sampled_wall]))
            strictcover={str(e):float(np.sum(wweights[wd<=e])/wall_area) for e in [1,2]}
        nearest_sample_index=cKDTree(p).query(wworld,workers=1)[1]
        source_hashes_after={p:sha(Path(p)) for p in plan['hashes_before']}
        assert source_hashes_after==plan['hashes_before']
        result={'dataset':ds,'case_id':cid,'raw_voxel_shape':list(shape),'voxel_counts':counts,
                'spacing_mm':np.linalg.norm(directions,axis=1).tolist(),'space_directions':directions.tolist(),'space_origin':orig.tolist(),
                'partition_exact':True,'raw_complete_mask_fingerprint_sha256':mask_hash(c),
                'boundary_voxel_counts':{**boundary_counts,'defective':boundary_summary['boundary_voxels']},
                'defective_boundary_voxel_center_coverage':boundary_summary,
                'defective_exposed_voxel_faces':nfaces,'defective_voxel_face_area_mm2':total_area,
                'defective_face_area_coverage_at_1mm':float(whole_cover[0]/total_area),
                'defective_face_area_coverage_at_2mm':float(whole_cover[1]/total_area),
                'cut_interface_faces':wallfaces,'cut_interface_voxel_face_area_mm2':wall_area,
                'cut_interface_area_coverage_all_input_at_1mm':float(wall_cover[0]/wall_area),
                'cut_interface_area_coverage_all_input_at_2mm':float(wall_cover[1]/wall_area),
                'cut_interface_area_coverage_cut_adjacent_input_only':strictcover,
                'cut_adjacent_defective_boundary_voxels':int(wall.sum()),
                'sampled_cut_adjacent_voxel_centers':int(sampled_wall.sum()),
                'sampled_cut_adjacent_fraction':float(sampled_wall.mean()),
                'nearest_cut_face_input_distance_mm':describe(face_coverage(wworld,tree)),
                'wall_area_nearest_sample_is_cut_adjacent_fraction':float(np.sum(wweights[sampled_wall[nearest_sample_index]])/wall_area),
                'dense_cutface_2mm_band_points':int(denseband.sum()),'sparse_implant_2mm_band_points':int(sparseband.sum()),
                'band_overlap_points':int((denseband&sparseband).sum()),
                'dense_band_only_points':int((denseband&~sparseband).sum()),
                'sparse_band_only_points':int((sparseband&~denseband).sum()),
                'input_hashes_after_match':True,'hashes_after':source_hashes_after,
                'max_voxel_center_reprojection_error_index_units':float(np.max(np.abs(pidx-pint))),
                'inner_outer_surface_semantics':'Not globally labelled; raw sections provided, no radial-normal pseudo-labels'}
        picture(ds,cid,d,g,wall,pidx,directions)
        dump(OUT/(ds+'_'+cid+'_metrics.json'),result)
        results.append(result)
        print('DONE',ds,cid,'boundary=',boundary_summary['boundary_voxels'],'wall_sample=',int(sampled_wall.sum()),'wall_cov2=',wall_cover[1]/wall_area,flush=True)
        del masks,c,d,g,wall,wworld,wallcoords,wallweights,wweights,p,pidx,pint,tree
        gc.collect()
    dump(OUT/'results.json',{'status':'COMPLETED_SIX_RAW_PAIRS_MUG_STL_STILL_MISSING','cases':results,
                           'elapsed_seconds':time.time()-start,'python':sys.version,'numpy':np.__version__,
                           'sanity_checks':sanity,'source_inputs_unchanged':True,'server_operations':0,
                           'model_imports':0,'gpu_operations':0,'source_resampling':0,
                           'limitations':['Voxel-face-center quadrature is resolution- and orientation-dependent, not smooth anatomical area.',
                                          'Euclidean coverage may cross nearby sheets; strict cut-adjacent-only coverage is also provided.',
                                          'Semantic outer/inner cortical labels and continuous closed-mesh topology are not established.',
                                          'Original source coordinate geometry preserved; no grid upsampling.',
                                          'Only the original six selected training cases.']})
    fields=['dataset','case_id','boundary_voxels','cut_faces','cut_area_mm2','sampled_cut_voxels','global_face_coverage_2mm','cut_face_coverage_2mm','strict_cut_coverage_2mm','dense_band_points','sparse_band_points']
    with (OUT/'summary.csv').open('x',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=fields)
        writer.writeheader()
        for r in results:
            writer.writerow(dict(zip(fields,[r['dataset'],r['case_id'],r['boundary_voxel_counts']['defective'],r['cut_interface_faces'],r['cut_interface_voxel_face_area_mm2'],r['sampled_cut_adjacent_voxel_centers'],r['defective_face_area_coverage_at_2mm'],r['cut_interface_area_coverage_all_input_at_2mm'],r['cut_interface_area_coverage_cut_adjacent_input_only']['2'],r['dense_cutface_2mm_band_points'],r['sparse_implant_2mm_band_points']])))
    with (OUT/'files.sha256').open('x') as f:
        for p in sorted(OUT.iterdir()):
            if p.is_file() and p.name!='files.sha256':
                f.write(sha(p)+'  '+p.name+'\n')
    print('COMPLETED_SIX_RAW_PAIRS_MUG_STL_STILL_MISSING',flush=True)

if __name__=='__main__':
    try:
        main()
    except Exception as e:
        if OUT.exists() and not (OUT/'failure.json').exists():
            dump(OUT/'failure.json',{'status':'STOPPED','type':type(e).__name__,'error':str(e)})
        raise
