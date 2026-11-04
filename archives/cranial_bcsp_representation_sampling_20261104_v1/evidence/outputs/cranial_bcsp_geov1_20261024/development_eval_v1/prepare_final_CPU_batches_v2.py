"""Version CPU fixtures only; preserve prior results and Linux production flags."""
from pathlib import Path
N=Path(__file__).resolve().parent
s=(N/'test_prediction_and_score_v1.py').read_text().replace("F=N/'cpu1'","F=N/'cpu2'").replace('prediction_score_CPU_result_v1.json','prediction_score_CPU_result_v2.json')
with (N/'test_prediction_and_score_v2.py').open('x') as f:f.write(s)
s=(N/'test_controller_v1.py').read_text().replace("F=N/'ctrlcpu1'","F=N/'ctrlcpu2'").replace('controller_CPU_result_v1.json','controller_CPU_result_v2.json')
s=s.replace('from pathlib import Path','from pathlib import Path\nfrom unittest.mock import patch')
s=s.replace("  p=F/'one.txt';c.create(p,b'original')\n  with self.assertRaises(FileExistsError):c.create(p,b'changed')", "  p=F/'one.txt'\n  # Windows lacks O_NOFOLLOW: emulate only the flag constant for this fixture.\n  # Production retains O_NOFOLLOW and Linux path checks; this is not a Linux symlink proof.\n  with patch.object(c.os,'O_NOFOLLOW',getattr(c.os,'O_NOFOLLOW',0),create=True):\n   c.create(p,b'original')\n   with self.assertRaises(FileExistsError):c.create(p,b'changed')")
with (N/'test_controller_v2.py').open('x') as f:f.write(s)
