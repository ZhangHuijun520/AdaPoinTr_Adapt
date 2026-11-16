from pathlib import Path
import os
os.environ['MPLBACKEND']='Agg'
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json,hashlib
D=Path(__file__).resolve().parent;r=json.loads((D/'stage_diagnostic_result_v1.json').read_bytes());assert all(r['checks'].values())
fig,axs=plt.subplots(11,2,figsize=(11,23),layout='constrained')
for i,c in enumerate(r['cases']):
 for j,(metric,label) in enumerate([('centroid_offset_mm','Centroid error (mm)'),('E_P95_mm','A1 E_P95 (mm)')]):
  ax=axs[i,j]
  for arm,col in [('RF-Static','#0072B2'),('RF-Requery','#D55E00')]:
   rows=[x for x in r['records'] if (x['fold'],x['case_id'],x['arm'])==(c['fold'],c['case_id'],arm)];ax.plot(range(4),[x[metric] for x in rows],marker='o',color=col,label=arm,lw=1.5)
  ax.set_xticks(range(4),['Q0','Q1','Q2','dense']);ax.set_ylabel(label);ax.grid(alpha=.2);ax.set_ylim(bottom=0);ax.set_title(c['fold']+' '+c['case_id']+' | '+c['role'],fontsize=8)
  if i==0:ax.legend(fontsize=8)
fig.suptitle('RIVE fixed11 existing predictions | Posthoc stage geometry, not causal intervention\nSame axes per case in detailed XY/XZ/YZ panels; 256 coarse points vs8192 dense points.',fontsize=12)
fig.savefig(D/'fixed11_stage_trajectories_v1.png',dpi=130);plt.close(fig)
print('SUMMARY_TRAJECTORY_RENDERED')
