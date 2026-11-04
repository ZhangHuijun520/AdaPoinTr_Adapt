# -*- coding: utf-8 -*-
import os
os.environ.update(MPLBACKEND='Agg',OPENBLAS_NUM_THREADS='2')
from pathlib import Path
import json,hashlib,importlib.util
import numpy as np
from scipy.spatial import cKDTree
N=Path(__file__).resolve().parent;O=N/'input_interface_sampling_20261102_v1'
os.environ['MPLCONFIGDIR']=str(O/'mplconfig')
import matplotlib.pyplot as plt
rows=json.loads((O/'metrics.json').read_text());methods=['uniform8k','D_PCA_4k_plus_4k'];cases=list(dict.fromkeys(r['case'] for r in rows if not r['phantom']))
assert len(rows)==54 and len(cases)==6
def mean(rs,fn):return float(np.mean([fn(x) for x in rs]))
summary={}
for m in methods:
 r=[x for x in rows if not x['phantom'] and x['method']==m]
 summary[m]={k:mean(r,f) for k,f in {'J_cover2':lambda x:x['J']['cover_2mm'],'J_p95':lambda x:x['J']['p95_mm'],'E_cover2':lambda x:x['E']['cover_2mm'],'all_cover2':lambda x:x['all']['cover_2mm'],'J_points':lambda x:x['J_face_point_count'],'support_points':lambda x:x['support_2mm_center_reference_count'],'NN_median':lambda x:x['NN_spacing_median_mm']}.items()}
# Verify saved inputs and final frozen target identities, without re-sampling.
for p in O.glob('*.npz'):
 a=np.load(p);assert a['xyz'].shape==(8192,3) and np.isfinite(a['xyz']).all()
bindings={r['target']['path']:r['target']['sha256'] for r in rows if not r['phantom']}
for path,digest in bindings.items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest
(O/'summary.json').write_text(json.dumps(summary,indent=2))
# Analytic phantom inner/outer E reference distinction, seed0 saved inputs only.
sp=importlib.util.spec_from_file_location('geo',N/'cpu_geometry_package_v1.py');geo=importlib.util.module_from_spec(sp);sp.loader.exec_module(geo)
layer=[]
for h,phase,angle in [(1.,0.,0.),(.7,.23,.4),(1.2,.31,.7)]:
 a=np.arange(-24,24+h,h);x=np.stack(np.meshgrid(a,a,a,indexing='ij'),-1)+phase*h;r=np.linalg.norm(x,axis=-1);C=(r<=20)&(r>=17);G=C&(x@np.array([np.cos(angle),np.sin(angle),0])>10);D=C&~G
 S=geo.surf(D,G,np.eye(3)*h,np.full(3,a[0]+phase*h));rr=np.linalg.norm(S[0],axis=1);inner=(abs(rr-17)<abs(rr-20))&~S[2];outer=~inner&~S[2]
 for m in methods:
  p=np.load(O/('phantom_'+str(h)+'_'+m+'.npz'))['xyz'];d=cKDTree(p).query(S[0])[0]
  layer.append({'spacing':h,'method':m,'seed':0,'inner_cover1':float(np.average(d[inner]<=1,weights=S[3][inner])),'outer_cover1':float(np.average(d[outer]<=1,weights=S[3][outer])),'labels':'analytic shell radii nearest 17/20 mm; voxel face-center quadrature'})
(O/'phantom_layer_metrics.json').write_text(json.dumps(layer,indent=2))
fig,axes=plt.subplots(2,2,figsize=(12,8),constrained_layout=True)
for ax,key,fn,title in [(axes[0,0],'J_cover2',lambda x:100*x['J']['cover_2mm'],'Cutwall coverage at 2 mm (%)'),(axes[0,1],'J_p95',lambda x:x['J']['p95_mm'],'Cutwall P95 (mm; lower is better)'),(axes[1,0],'all_cover2',lambda x:100*x['all']['cover_2mm'],'Whole D coverage at 2 mm (%)'),(axes[1,1],'J_points',lambda x:x['J_face_point_count'],'Sample points on cutwall')]:
 for m,col in zip(methods,['#2676b8','#d55e00']):
  y=[mean([r for r in rows if r['case']==c and r['method']==m],fn) for c in cases];ax.plot(range(6),y,'o-',color=col,label=m)
 ax.set_xticks(range(6),['SF002','SF003','SF004','SB000','SB001','SB002']);ax.set_title(title);ax.grid(alpha=.2)
axes[0,0].legend();fig.suptitle('D-only curvature enhancement fails in this fixed six-case pilot\nEach point is the mean of 3 sampling seeds; no model or training')
fig.savefig(O/'paired_geometry_results.png',dpi=150);plt.close(fig)
lines=['# 固定六例 D-only 接口采样比较报告','日期：2026-11-02。六例既有开发来源、三组既有解析球壳离散设置，各 3 个 sampling seed；无训练／GPU／服务器。','## 结论','**本次固定 PCA 曲率增强候选失败，不进入训练，也不作为新默认采样器。六例的切壁和全局覆盖均下降。**失败仅否定本轮具体算法与固定配额，不能推广为所有局部采样方法无效。','## 冻结方法','输入均为 8,192 点。对照为既有 V1 全表面物理面积均匀采样；候选由 4,096 全局均匀点和 4,096 局部增强点组成。局部定位仅使用 D：先面积均匀采 32,768 候选点，计算 32 近邻局部协方差，以最小特征值／特征值和为曲率分数，选最高约 10% 区域，再在选中体素面内重新均匀取点。没有改邻域、阈值或配额进行扫描。','函数仅接收 D 的面中心、面轴、面积、affine 与 seed。真实病例全部三 seed 选点完成后，才读取 G/C 几何进行评价。J／R／G 不用于局部定位；该隔离为代码调用合同，不宣称进行了操作系统级访问隔离。目标沿用六例既有 G_V1_8192 点集，最终重新核对其 SHA256；本轮没有重新采目标。','## 六例等权描述性结果','每例先平均三个 seed，再六例等权；由于每例均三个 seed，等同于对应 18 行平均。P95 是逐例逐 seed P95 的平均，不是合并全体面的 P95；sampling seed 不作为独立病例或训练重复。','|指标|全局均匀8k|D-only PCA增强8k|','|---|---:|---:|']
for title,k,scale in [('切壁 Cover@2mm，%','J_cover2',100),('切壁 P95，mm','J_p95',1),('原生表面 E Cover@2mm，%','E_cover2',100),('全边界 Cover@2mm，%','all_cover2',100),('切壁采样点数','J_points',1),('距切壁面中心≤2mm点数','support_points',1),('最近邻间距中位数，mm','NN_median',1)]:lines.append('|%s|%.4f|%.4f|'%(title,summary[methods[0]][k]*scale,summary[methods[1]][k]*scale))
lines+=['## 定位及层面覆盖的解释','最高曲率候选中，到真实切壁面中心≤2mm的比例六例三seed平均仅约 0.417%。曲率对缺损接口缺乏专属性，可能优先选中其他曲面变化和薄层邻域混合区域；本轮没有对所有误选部位做解剖标注，因此不将其统一归因为颅底或噪声。局部重复选面减少了全局有效覆盖。','真实六例仅有 E/J 几何来源标签，无可靠解剖内外板标签，故不虚构真实内外板覆盖率。解析球壳可按 17/20mm 内外半径分层，seed0 的内外层 Cover@1mm 另存 phantom_layer_metrics.json；该标签仅适用于解析模型。球壳尺度小、8k 已较密，Cover@2mm 接近饱和，不能以其通过证明真实接口定位成功。','评价使用全部暴露体素面中心及物理面积作为积分近似，距离和覆盖不是连续表面的精确值。接口支持点数参照切壁面中心，也不是严格连续切壁距离。没有做统计显著性、临床准确性或正式 gate 判断。','## 科研决定','保留全局均匀8k作为当前几何基线，保留原四运行输入密度结果；不追加训练。停止本候选的自动调参和逐点修补。下一步应先查看既有模型在接口的预测误差及 proxy 取点，区分“输入已经包含但模型丢失”与“原始接口支持不足”，再决定是否值得设计专门的 D-only 接口定位。','A0221 不加入本次六例比较，保持其前景质量限制记录。前景清理与接口采样是两个问题，不能靠强化采样掩盖分割伪影。','## 核验与产物','主体进程 exit code 0，completion.json：6真实病例＋3 phantom，共54条方法／seed结果，主体81.875秒。保存18份seed0输入点集，均核对8192×3及有限值；六个目标SHA256再次匹配。18个原始NRRD在评价阶段匹配原scope哈希，源目录没有写入。无模型加载、checkpoint或训练。','本轮为一次限定科研诊断，不宣称完成通用生产P3。配对图已另行视觉检查；脚本、协议、原始指标、目标绑定与phantom分层结果均保留。']
(O/'report_zh_v1.md').write_text('\n\n'.join(lines),encoding='utf-8')
print(json.dumps(summary))
