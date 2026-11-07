"""Reuse independent standard-library audit helpers, not scorer or metric imports."""
import ast
from pathlib import Path
S=Path(__file__).resolve().parent;P=S.parent/'H1_scoring_implementation_20261107_v1/audit_H1_M0_scores_v1.py'
t=P.read_text(encoding='utf-8');t=t[:t.index('def main():')]
t=t.replace('Independent read-only H1/M0 freeze audit','Independent read-only H2 three-arm freeze audit').replace('a962c57510371c880fa3510a56c2ffe4081537201797210a5769558dd07f94ab','3531fa8ca3282a7896be7df2b501be0ec1687f0448ebe7a613d2414e32d4f2b3').replace("ARMS=['M0','M_H1'];ALL=","ARMS=['M0','H2_AUX','H2_COUPLE'];PAIRS=[('H2_AUX','H2_COUPLE'),('M0','H2_COUPLE'),('M0','H2_AUX')];ALL=")
t=t.replace('def risk_table(rows,ids):','def risk_table(rows,ids,pair):').replace("for arm in ARMS];records.append(dict(case_id=cid,source_id='train:'+cid.split('__')[1],defect=cid.split('__',2)[-1],M0=a,M_H1=b,new=b and not a,rescued=a and not b))","for arm in pair];records.append(dict(case_id=cid,source_id='train:'+cid.split('__')[1],defect=cid.split('__',2)[-1],baseline_arm=pair[0],candidate_arm=pair[1],baseline=a,candidate=b,new=b and not a,rescued=a and not b))")
t=t.replace("M0_count=sum(r['M0'] for r in records),M_H1_count=sum(r['M_H1'] for r in records)","baseline_arm=pair[0],candidate_arm=pair[1],baseline_count=sum(r['baseline'] for r in records),candidate_count=sum(r['candidate'] for r in records)")
body=(S/'independent_score_audit_body_v1.txt').read_text(encoding='utf-8');t+=body;ast.parse(t)
with (S/'audit_H2_three_arm_scores_v1.py').open('x',encoding='utf-8',newline='\n') as f:f.write(t)
print('INDEPENDENT_READONLY_AUDIT_STATIC_PASS')
