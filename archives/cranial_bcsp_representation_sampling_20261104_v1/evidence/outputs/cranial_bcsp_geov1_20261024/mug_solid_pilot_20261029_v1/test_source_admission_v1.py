import gzip,io,json,struct,sys,unittest
from pathlib import Path
N=Path(__file__).resolve().parent;sys.path.insert(0,str(N))
import numpy as np
import source_admission_v1 as m
def blob(data,shape=None):
 shape=shape or data.shape
 head='NRRD0004\ntype: short\ndimension: 3\nspace: left-posterior-superior\nsizes: '+' '.join(map(str,shape))+'\nspace directions: (0,2,0) (0,0,-3) (-4,0,0)\nspace origin: (5,6,7)\nendian: little\nencoding: gzip\n\n'
 return head.encode()+gzip.compress(data.astype('<i2').tobytes(order='F'))
class Source(unittest.TestCase):
 def test_01_exact_signed_scalar_F_order(self):
  x=np.arange(-12,12,dtype=np.int16).reshape(2,3,4);a,_,_,_=m.decode_nrrd(blob(x));np.testing.assert_array_equal(a,x)
 def test_02_declared_size_mismatch_stops(self):
  with self.assertRaises(ValueError):m.decode_nrrd(blob(np.zeros((2,3,4)),(2,3,5)))
 def test_03_unsigned_or_detached_not_silently_converted(self):
  x=blob(np.zeros((2,3,4)))
  with self.assertRaises(ValueError):m.decode_nrrd(x.replace(b'type: short',b'type: ushort'))
 def test_04_nonbinary_not_mask(self):
  stats,_,_=m.histogram(np.array([-1024,-500,0,30,600,1500],np.int16));self.assertFalse(stats['binary_value_candidate']);self.assertEqual(stats['unique_values'],6)
 def test_05_binary_values_not_semantic_proof(self):
  stats,_,_=m.histogram(np.array([0,0,1],np.int16));self.assertTrue(stats['binary_value_candidate']);self.assertEqual(stats['label_semantics'],'UNCONFIRMED_NO_BONE_MASK_METADATA')
 def test_06_affine_and_two_slice_span(self):
  _,a,o,_=m.decode_nrrd(blob(np.zeros((2,3,4))));b=m.physical_bounds((2,3,4),a,o)
  self.assertEqual(b['axis_center_lengths_mm'],[2.,6.,12.]);self.assertEqual(b['minimum'],[-7.,6.,1.])
 def test_07_binary_STL_vertices_and_hash(self):
  dt=np.dtype([('n','<f4',(3,)),('v','<f4',(3,3)),('a','<u2')]);r=np.zeros(1,dt);r['v'][0]=[[1,2,3],[3,2,3],[1,4,3]]
  raw=b' '*80+struct.pack('<I',1)+r.tobytes();b=m.stl_bounds(io.BytesIO(raw),len(raw));self.assertEqual(b['span_mm'],[2.,2.,0.]);self.assertEqual(b['sha256'],m.h(raw))
 def test_08_wrong_STL_record_count(self):
  with self.assertRaises(ValueError):m.stl_bounds(io.BytesIO(b' '*80+struct.pack('<I',2)),84)
if __name__=='__main__':
 r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Source))
 m.dump(N/'artificial_CPU_tests_v1.json',dict(status='PASS' if r.wasSuccessful() else 'FAILED_STOP',tests=r.testsRun,failures=len(r.failures),errors=len(r.errors),real_source_reads=0,server_calls=0,GPU_calls=0,implementation_sha256=m.h(Path(m.__file__).read_bytes())))
 raise SystemExit(0 if r.wasSuccessful() else 1)
