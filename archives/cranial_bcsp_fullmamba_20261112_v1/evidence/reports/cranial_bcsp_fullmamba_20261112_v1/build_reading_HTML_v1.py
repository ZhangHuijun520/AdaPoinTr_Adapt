"""Offline report reading copy with embedded figures/formulae; no research computation."""
import os
from pathlib import Path
S=Path(__file__).resolve().parent
os.environ.update(MPLCONFIGDIR=str(S/'report_font_cache_v1'),MPLBACKEND='Agg',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2')
import base64,hashlib,html,io,json,re
from urllib.parse import unquote
import markdown
from matplotlib.mathtext import math_to_image
name='Cranial_BCSP_FullMamba_本轮完整实验报告_zh_2026-11-12_v1'
raw=(S/(name+'.md')).read_text(encoding='utf-8');placeholders={};formulas=[]
def formula(match):
 tex=' '.join(match.group(1).split());key='REPORTFORMULA'+str(len(placeholders))
 try:
  # Equivalent explicit braces for matplotlib's narrower TeX parser; definitions unchanged.
  render_tex=tex.replace(r'\mathcal N',r'\mathcal{N}').replace(r'\frac12',r'\frac{1}{2}').replace(r'\frac1{',r'\frac{1}{').replace(r'\|',r'\Vert ')
  buf=io.BytesIO();math_to_image('$'+render_tex+'$',buf,format='svg',dpi=150,color='#0f172a')
  svg=buf.getvalue().decode();svg=svg[svg.index('<svg'):]
  placeholders[key]='<div class="formula" aria-label="'+html.escape(tex,quote=True)+'">'+svg+'</div>';status='SVG'
 except Exception:
  placeholders[key]='<pre class="formula-source">'+html.escape(tex)+'</pre>';status='LaTeX source'
 formulas.append(dict(formula=tex,status=status));return '\n\n'+key+'\n\n'
text=re.sub(r'\\\[(.*?)\\\]',formula,raw,flags=re.S)
md=markdown.Markdown(extensions=['tables','fenced_code','toc']);body=md.convert(text)
for key,val in placeholders.items():body=body.replace('<p>'+key+'</p>',val)
def assets(match):
 attr,url=match.group(1),html.unescape(unquote(match.group(2)))
 if re.match(r'^[A-Za-z]:/',url):
  p=Path(url)
  if attr=='src' and p.suffix.lower()=='.png':return 'src="data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode()+'"'
  return attr+'="'+html.escape(os.path.relpath(p,S).replace('\\','/'),quote=True)+'"'
 return match.group(0)
body=re.sub(r'\b(href|src)="([^"]+)"',assets,body)
# The Markdown keeps the canonical Mermaid source. The reading copy embeds its fixed completed-stage map.
labels=['固定任务与替换边界','F0：准入、两折训练、Native评分','30次decoder-only条件诊断','LQI：唯一公式、准入、两折训练','LQI／F0统一评分与正式冻结审计','七病例几何诊断 → 本轮正式收束','下一阶段coarse位置／范围假设（仅建议）']
svg=['<svg viewBox="0 0 920 490" role="img" aria-label="本轮科研闭环" style="max-width:950px;width:100%;height:auto"><defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L6,3 z" fill="#475569"/></marker></defs>']
for i,label in enumerate(labels):
 y=8+i*68;color='#e0f2fe' if i<6 else '#f1f5f9';stroke='#0284c7' if i<6 else '#94a3b8'
 svg.append(f'<rect x="100" y="{y}" width="720" height="47" rx="8" fill="{color}" stroke="{stroke}"/><text x="460" y="{y+29}" text-anchor="middle" font-size="18" fill="#0f172a">{html.escape(label)}</text>')
 if i<6:svg.append(f'<line x1="460" y1="{y+47}" x2="460" y2="{y+65}" stroke="#475569" marker-end="url(#arrow)"/>')
svg.append('</svg>')
body=re.sub(r'<pre><code class="language-mermaid">.*?</code></pre>',''.join(svg),body,flags=re.S)
css='''body{font:17px/1.8 "Microsoft YaHei",system-ui,sans-serif;color:#162236;background:#f1f5f9;margin:0}main{max-width:1240px;margin:24px auto;background:white;padding:46px 54px;box-shadow:0 3px 20px #0f172a12}h1{font-size:30px;line-height:1.4}h2{margin-top:2.2em;padding-bottom:8px;border-bottom:2px solid #dbeafe;color:#0c4a6e}h3{margin-top:1.6em}table{width:100%;border-collapse:collapse;font-size:13px;line-height:1.7;margin:18px 0;table-layout:auto}th,td{padding:9px 10px;border:1px solid #cbd5e1;vertical-align:top;overflow-wrap:anywhere}th{background:#e8f2fb;text-align:left}tr:nth-child(even){background:#f8fafc}a{color:#0369a1;text-decoration:none}a:hover{text-decoration:underline}code{font:12px/1.6 Consolas,monospace;overflow-wrap:anywhere;background:#f1f5f9;padding:1px 3px}pre{white-space:pre-wrap;border:1px solid #cbd5e1;padding:14px;background:#f8fafc}img{max-width:100%;height:auto;border:1px solid #e2e8f0}.formula{overflow-x:auto;text-align:center;padding:18px;background:#fafcff}.formula svg{max-width:100%;height:auto}.toc{font-size:14px;background:#f0f9ff;border:1px solid #bae6fd;padding:12px 20px;column-count:2}.toc ul{padding-left:20px}.notice{font-size:14px;color:#475569;background:#f8fafc;padding:10px 14px}@media print{body{background:white;font-size:11pt}main{max-width:none;margin:0;padding:0;box-shadow:none}.toc{column-count:2}h2,h3{break-after:avoid}tr,img,.formula{break-inside:avoid}a{color:#162236}}'''
page='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Cranial-BCSP-FullMamba 本轮完整实验报告</title><style>'+css+'</style></head><body><main><p class="notice">本机离线阅读版｜2026-11-12｜正文与Markdown正式版一致；核心图片与公式内嵌，证据文件链接依赖原本机目录。未新增实验或评分。</p>'+md.toc+body+'</main></body></html>'
with (S/(name+'.html')).open('w',encoding='utf-8') as f:f.write(page)
with (S/'HTML_reading_copy_validation_v1.json').open('w',encoding='utf-8') as f:json.dump(dict(status='OFFLINE_READING_COPY_GENERATED',source_markdown_sha256=hashlib.sha256((S/(name+'.md')).read_bytes()).hexdigest(),html_sha256=hashlib.sha256((S/(name+'.html')).read_bytes()).hexdigest(),formulae=formulas,embedded_PNG=page.count('data:image/png;base64,'),external_script_tags=page.lower().count('<script src='),browser_visual_QA=False,scientific_values_changed=False),f,ensure_ascii=False,indent=2)
print(json.dumps(dict(status='HTML_READING_COPY_WRITTEN',formulae=[x['status'] for x in formulas],bytes=len(page.encode()),embedded_PNG=2)))
