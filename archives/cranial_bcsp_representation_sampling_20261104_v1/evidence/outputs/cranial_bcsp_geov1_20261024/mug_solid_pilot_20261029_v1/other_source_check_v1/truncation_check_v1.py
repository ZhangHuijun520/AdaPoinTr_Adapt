"""Read-only component/boundary diagnostics; labels never replace source mask."""
import os
os.environ.update(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
import json,sys,zipfile,gc,hashlib
from pathlib import Path
import numpy as np
from scipy import ndimage
N=Path(__file__).resolve().parent
sys.path.insert(0,str(N.parent))
from source_admission_v1 import decode_nrrd
rows=[]
for s in json.loads((N/'results.json').read_text()):
    with zipfile.ZipFile(s['archive']) as z:b=z.read(s['member'])
    assert hashlib.sha256(b).hexdigest()==s['sha256']
    a,A,o,f=decode_nrrd(b);mask=a.astype(bool);del a,b
    labels,n=ndimage.label(mask,structure=ndimage.generate_binary_structure(3,1))
    counts=np.bincount(labels.ravel());counts[0]=0;main=int(counts.argmax());contacts=[]
    for axis in range(3):
        for side,pos in [('low',0),('high',mask.shape[axis]-1)]:
            sl=[slice(None)]*3;sl[axis]=pos;plane=labels[tuple(sl)];ij=np.argwhere(plane==main)
            if len(ij):
                idx=np.empty((len(ij),3));idx[:,axis]=pos;idx[:,[k for k in range(3) if k!=axis]]=ij;w=idx@A+o
                world={'min_LPS':w.min(0).tolist(),'max_LPS':w.max(0).tolist(),'count_at_z_ge_30mm':int((w[:,2]>=30).sum())}
            else:world=None
            contacts.append({'axis':axis,'side':side,'main_component_contact_voxels':len(ij),'world':world})
    row={'source_id':s['id'],'connectivity':6,'component_count':int(n),'main_component_voxels':int(counts[main]),'main_component_fraction_of_foreground':float(counts[main]/mask.sum()),'top10_component_voxel_counts':np.sort(counts)[-10:][::-1].tolist(),'contacts':contacts,'z_ge_30mm_is_descriptive_calvarial_screen_not_anatomical_label':True,'components_removed':0}
    rows.append(row);print(json.dumps(row),flush=True);del mask,labels,counts;gc.collect()
with (N/'geometry_results_v2'/'truncation_components.json').open('x') as f:json.dump(rows,f,indent=2)
