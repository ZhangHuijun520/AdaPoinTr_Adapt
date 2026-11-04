"""Artificial geometry contracts; fixed existing CPU environment only."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
os.environ['OMP_NUM_THREADS']='2';os.environ['OPENBLAS_NUM_THREADS']='2'
import hashlib,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np
import bcsp_eval_metrics_v1 as m

class Geometry(unittest.TestCase):
 def setUp(self):
  self.g=np.zeros((5,5,5),bool);self.g[2,2,2]=True
  self.d=np.zeros_like(self.g);self.d[1,2,2]=True
  self.a=np.diag([2.,3.,4.]);self.o=np.array([11.,-7.,5.])
  self.r=m.surface_references(self.g,self.d,self.a,self.o)
 def test_01_anisotropic_face_area(self):
  self.assertEqual(len(self.r['a_centers']),6)
  self.assertEqual(self.r['a_weights'].sum(),52)
  self.assertEqual(self.r['a_weights'][self.r['a_is_j']].sum(),12)
 def test_02_J_and_native_partition(self):
  self.assertEqual(self.r['a_is_j'].sum(),1)
  self.assertEqual((~self.r['a_is_j']).sum(),5)
 def test_03_world_frame(self):
  np.testing.assert_allclose(self.r['a_centers'].mean(0),np.array([2,2,2])@self.a+self.o)
 def test_04_rotated_reflected_frame(self):
  transform=np.array([[0.,1,0],[1,0,0],[0,0,-1]])
  r=m.surface_references(self.g,self.d,self.a@transform,self.o)
  np.testing.assert_allclose(r['a_weights'],self.r['a_weights'])
  np.testing.assert_allclose(r['a_centers'],(self.r['a_centers']-self.o)@transform+self.o)
 def test_05_A2_area_conservation(self):
  x,w,j=m.a2_reference(self.r)
  self.assertEqual(len(x),24);self.assertEqual(w.sum(),52);self.assertEqual(w[j].sum(),12)
 def test_06_area_weighted_P95(self):
  self.assertEqual(m.weighted_quantile([0,10],[99,1]),0)
  self.assertEqual(m.weighted_quantile([0,10],[1,1]),10)
 def test_07_inclusive_coverage(self):
  self.assertEqual(m.stats([.5,1,2])['coverage']['2.0'],1)
  self.assertEqual(m.stats([.5,1,2])['coverage']['0.5'],1/3)
 def test_08_euclidean_not_squared(self):
  np.testing.assert_array_equal(m.nearest([[0,0,0]],[[3,4,0]]),[5])
 def test_09_normalization_to_mm(self):
  np.testing.assert_array_equal(m.world_points([[1,2,3]],dict(center=[2,3,4],scale=2)),[[4,7,10]])
 def test_10_MC_positive_world_area(self):
  self.assertTrue((self.r['b_weights']>0).all())
  self.assertTrue(np.isfinite(self.r['b_centers']).all())
  self.assertLess(self.r['b_weights'].sum(),52)
 def test_11_invalid_prediction_retained(self):
  r=m.score_cloud(np.empty((0,3)),self.r,np.zeros((1,3)))
  self.assertEqual(r['status'],'INVALID_PREDICTION');self.assertEqual(r['primary_E_G_P95_mm'],np.inf)
  self.assertEqual(r['regions']['A1']['J']['coverage']['2.0'],0)
 def test_12_nonfinite_prediction(self):
  r=m.score_cloud([[np.nan,0,0]],self.r,np.zeros((1,3)))
  self.assertEqual(r['status'],'INVALID_PREDICTION')
 def test_13_empty_region_NA(self):
  self.assertIsNone(m.stats([])['p95_mm'])
 def test_14_CD_half_sum(self):
  r=m.score_cloud([[0,0,0]],self.r,[[3,4,0]])
  self.assertEqual(r['CD_L1_mm'],5)
 def test_15_bootstrap_determinism(self):
  self.assertEqual(m.paired_bootstrap([-1,0,2]),m.paired_bootstrap([-1,0,2]))
 def test_16_bootstrap_no_nonfinite_drop(self):
  r=m.paired_bootstrap([1,np.inf]);self.assertEqual(r['source_count'],2);self.assertIsNone(r['CI95'])
 def test_17_overlap_rejected(self):
  with self.assertRaises(ValueError):m.surface_references(self.g,self.g,self.a,self.o)
 def test_18_GT_reference_validation(self):
  with self.assertRaises(ValueError):m.score_cloud([[0,0,0]],self.r,[])
 def test_19_JSON_failure_encoding(self):
  self.assertEqual(m.json_safe(dict(x=float('inf'))),dict(x='POS_INF'))
 def test_20_duplicate_counts(self):
  r=m.score_cloud([[0,0,0],[0,0,0]],self.r,[[0,0,0]])
  self.assertEqual(r['duplicate_points'],1)

if __name__=='__main__':
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Geometry))
 p=Path(__file__).with_name('geometry_CPU_contract_result_v1.json')
 with p.open('x') as f:json.dump(dict(status='PASS' if result.wasSuccessful() else 'FAILED_STOP',tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),CUDA_VISIBLE_DEVICES=os.environ['CUDA_VISIBLE_DEVICES'],versions=dict(python=sys.version,numpy=np.__version__),source_sha256=hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest()),f,indent=2)
 raise SystemExit(0 if result.wasSuccessful() else 1)
