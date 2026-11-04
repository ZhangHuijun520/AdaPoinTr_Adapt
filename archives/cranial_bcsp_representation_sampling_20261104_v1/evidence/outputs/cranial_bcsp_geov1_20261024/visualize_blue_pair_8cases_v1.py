"""Fixed eight-case existing-prediction review; reuse established plotting geometry."""
import ast
from pathlib import Path
B=Path(__file__).resolve().parent
p=B/'visualize_sampling_pair_8cases_v1.py';s=p.read_text(encoding='utf-8')
changes=[
('sampling_model_AB_foldC_seed0_20261103_v1/paired_development_eval_v1','blue_pair_eval_v1'),
("SOURCES=['051','053','013','041']","SOURCES=['081','042','051','013']"),
('0748d8e99c6589e47195a255abaf58f77751941e17c71e5e6ddb7c456ff059fa','a2a24869ca8b7300e1a804359c0a542bcba8473189eaa8f28d0c5aabb9e8bbe8'),
('two regressed sources051/053 and two improved013/041','two regressed sources081/042 and two improved051/013'),
("'V1'","'Euclidean_elimination'"),('Morton_area_stratified8k','surface_graph'),
('V1 blue / Morton orange','Euclidean blue / Graph orange'),
('V1 context','Euclidean common context'),('V1残缺骨点集','欧氏残缺骨点集'),
('Morton−V1','Graph−Euclidean'),('V1／Morton','欧氏／图距离'),
("subplot_titles=['Euclidean_elimination','Morton area-stratified 8k']","subplot_titles=['Euclidean (8k)','Surface graph (8k)']"),
("('Euclidean_elimination' if a==0 else 'Morton')","('Euclidean' if a==0 else 'Graph')"),
("('Euclidean_elimination' if col==1 else 'Morton')","('Euclidean' if col==1 else 'Graph')"),
("('Euclidean_elimination' if arm=='Euclidean_elimination' else 'Morton')","('Euclidean' if arm=='Euclidean_elimination' else 'Graph')"),
("zip(ARMS,['Euclidean_elimination','Morton'])","zip(ARMS,['Euclidean','Graph'])"),
("(pred['Euclidean_elimination'],COLORS[0],'Euclidean_elimination',4)","(pred['Euclidean_elimination'],COLORS[0],'Euclidean',4)"),
("(pred[ARMS[1]],COLORS[1],'Morton',4)","(pred[ARMS[1]],COLORS[1],'Graph',4)"),
("ax.set_title('Full context: D grey / GT green / Euclidean blue / Graph orange')","ax.set_title('Full context\\nD grey / GT green / Euclidean blue / Graph orange')"),
("cbar=fig.colorbar(mapper,ax=axes[1:3],fraction=.025,pad=.035,extend='max');cbar.set_label('Nearest reference distance (mm); ≥20 saturated')","cax=fig.add_axes([.94,.59,.009,.29]);cbar=fig.colorbar(mapper,cax=cax,extend='max');cbar.set_label('Pred → A2 (mm; ≥20 clipped)',fontsize=8)"),
('right=.93,bottom=.105,top=.925,wspace=.25','right=.90,bottom=.105,top=.925,wspace=.28'),
("fig.savefig(V/(cid+'.png'),dpi=150)","fig.savefig(V/(cid+'.png'),dpi=150,bbox_inches='tight')")]
for old,new in changes:
    assert old in s,old;s=s.replace(old,new)
ast.parse(s)
exec(compile(s,str(p)+'[fixed-blue-eight-cases]','exec'),{'__file__':str(p),'__name__':'__main__'})
