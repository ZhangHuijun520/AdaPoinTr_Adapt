"""One finite-output regression after static review; retain passing v1 evidence."""
import ast
from pathlib import Path
S=Path(__file__).resolve().parent
s=(S/'test_h2_cpu_v1.py').read_text(encoding='utf-8')
s=s.replace('artificial_cpu_batch_v1','artificial_cpu_batch_v2').replace("'test_h2_cpu_v1.py'","'test_h2_cpu_v2.py'")
anchor="if __name__=='__main__':"
extra=''' def test33_AUX_eval_nonfinite_head_reject(self):
  m=model('AUX').eval();m.h2_range_head.bias.data.fill_(float('nan'));x,_=inputs()
  with self.assertRaises(ValueError):m(x)
'''
assert s.count(anchor)==1;s=s.replace(anchor,extra+anchor);ast.parse(s)
with (S/'test_h2_cpu_v2.py').open('x',encoding='utf-8',newline='\n') as f:f.write(s)
