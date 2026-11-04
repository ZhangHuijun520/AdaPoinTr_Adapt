"""Figure QA revision only: reserve independent colorbar space; same fixed8 data."""
import ast
from pathlib import Path
B=Path(__file__).resolve().parent
source=(B/'visualize_sampling_pair_8cases_v1.py').read_text(encoding='utf-8')
source=source.replace("V=N/'geometry_review_8cases_v1'","V=N/'geometry_review_8cases_v1'/'static_layout_v2'")
source=source.replace("ax.set_title('Full context: D grey / GT green / V1 blue / Morton orange')","ax.set_title('Full context\\nD grey / GT green / V1 blue / Morton orange')")
source=source.replace("cbar=fig.colorbar(mapper,ax=axes[1:3],fraction=.025,pad=.035,extend='max');cbar.set_label('Nearest reference distance (mm); ≥20 saturated')","cax=fig.add_axes([.94,.59,.009,.29]);cbar=fig.colorbar(mapper,cax=cax,extend='max');cbar.set_label('Pred → A2 (mm; ≥20 clipped)',fontsize=8)")
source=source.replace('right=.93,bottom=.105,top=.925,wspace=.25','right=.90,bottom=.105,top=.925,wspace=.28')
source=source.replace("fig.savefig(V/(cid+'.png'),dpi=150)","fig.savefig(V/(cid+'.png'),dpi=150,bbox_inches='tight')")
source=source.replace('   interactive(cid,d,gt,wall,pred,reverse,focus_limits,official)','   # Reuse the previously generated interactive HTML; no new HTML data rendering.')
source=source.replace("href=\"'+cid+'.html", "href=\"../'+cid+'.html")
ast.parse(source)
exec(compile(source,'same8case_visual_layout_revision_v2','exec'),{'__name__':'__main__','__file__':str(B/'visualize_sampling_pair_8cases_v1.py')})
