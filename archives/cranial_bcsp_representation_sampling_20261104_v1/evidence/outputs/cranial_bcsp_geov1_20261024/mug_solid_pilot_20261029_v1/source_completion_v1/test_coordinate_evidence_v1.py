import io,json,struct,sys,unittest
from pathlib import Path
N=Path(__file__).resolve().parent;sys.path.insert(0,str(N))
import numpy as np
import coordinate_evidence_v1 as c
class Coordinates(unittest.TestCase):
 def test_01_RAS_LPS_exact_inverse(self):
  p=np.array([1.,-2.,3.]);np.testing.assert_array_equal(c.T@(c.T@p),p);self.assertEqual(np.linalg.det(c.T),1)
 def test_02_ellipsoid_membership_invariance(self):
  center=np.array([3.,4.,5.]);p=np.array([4.,5.,6.]);frame=np.eye(3);r=np.array([2.,3.,4.])
  a=np.sum((((p-center)@frame)/r)**2);b=np.sum(((((c.T@p)-(c.T@center))@(c.T@frame))/r)**2);self.assertEqual(a,b)
 def test_03_exact_vertices_match(self):
  q=np.array([[1,2,3],[4,5,6]],np.float32).view('<u4');found=np.zeros(2,bool);c.match_exact(q,q,found);self.assertTrue(found.all())
 def test_04_float_neighbor_is_not_exact(self):
  q=np.array([[1,2,3]],np.float32);near=q.copy();near[0,0]=np.nextafter(near[0,0],np.float32(2));found=np.zeros(1,bool)
  c.match_exact(near.view('<u4'),q.view('<u4'),found);self.assertFalse(found.any())
 def test_05_original_header_and_stream(self):
  a=np.zeros(1,c.DT);a['v'][0]=[[1,2,3],[4,2,3],[1,5,3]];raw=b'3D Slicer output. SPACE=RAS'.ljust(80,b'\x00')+struct.pack('<I',1)+a.tobytes()
  q=np.ascontiguousarray(a['v'].reshape(-1,3)).view('<u4');r=c.inspect_original(io.BytesIO(raw),len(raw),q,lambda n:None)
  self.assertTrue(r['all_sampled_coordinates_found']);self.assertEqual(r['minimum'],[1.,2.,3.]);self.assertEqual(r['maximum'],[4.,5.,3.])
 def test_06_no_guess_from_missing_header(self):
  raw=b'VCG'.ljust(80,b' ')+struct.pack('<I',1)+bytes(50)
  with self.assertRaises(ValueError):c.inspect_original(io.BytesIO(raw),len(raw),np.zeros((1,3),np.uint32),lambda n:None)
if __name__=='__main__':
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Coordinates))
 c.emit(N/'CPU_tests.json',dict(status='PASS' if r.wasSuccessful() else 'FAILED_STOP',tests=r.testsRun,failures=len(r.failures),errors=len(r.errors),implementation_sha256=c.sha(Path(c.__file__)),real_source_reads=0,GPU_calls=0))
 raise SystemExit(0 if r.wasSuccessful() else 1)
