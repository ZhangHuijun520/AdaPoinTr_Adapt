import unittest
from types import SimpleNamespace

import numpy as np

from rbss_order_v1 import content_key, schedule, temporary_order
from rbss_p1_cuda_v1 import verdict


class Array(np.ndarray):
    device = "cpu"

    def __new__(cls, x):
        return np.asarray(x).view(cls)

    def contiguous(self):
        return self

    def flip(self, i):
        return Array(np.flip(self, i))


def lexicographic_order(pos):
    order = np.array([np.lexsort((np.arange(len(a)), a[:,2], a[:,1], a[:,0])) for a in pos])
    return order, np.argsort(order, axis=1)


def gather_tokens(x, order):
    return Array(np.take_along_axis(x, np.asarray(order)[...,None], axis=1))


class Mix:
    def __init__(self):
        self.calls = 0
        self.mixer = self.scan

    def scan(self, x):
        self.calls += 1
        return Array(np.cumsum(x, axis=1))

    def forward(self, x, pos):
        native = lexicographic_order(pos)
        a = gather_tokens(x, native[0])
        return gather_tokens((self.mixer(a)+self.mixer(a.flip(1)).flip(1))*0.5, native[1])


class Test(unittest.TestCase):
    def test_native_replacement_parity_and_scan_count(self):
        xyz = Array(np.random.default_rng(1).normal(size=(2,8,3)).astype("f4"))
        x = Array(np.random.default_rng(2).normal(size=(2,8,384)).astype("f4"))
        m = Mix()
        native = m.forward(x, xyz)
        torch = SimpleNamespace(float32=np.float32,isfinite=np.isfinite)
        with temporary_order(m,torch,lambda p,o,i:(o,i)):
            np.testing.assert_array_equal(native,m.forward(x,xyz))
        self.assertEqual(m.calls,4)
        self.assertNotIn("forward",m.__dict__)

    def test_alternate_order_reaches_scans_and_uses_inverse(self):
        xyz = Array(np.zeros((1,5,3),dtype="f4"))
        x = Array(np.broadcast_to(np.arange(5,dtype="f4")[None,:,None],(1,5,384)).copy())
        m = Mix()
        seen = []
        def scan(a):
            seen.append(a[0,:,0].tolist())
            return Array(a + np.arange(a.shape[1],dtype="f4")[None,:,None] ** 2)
        m.mixer=scan
        idx=np.array([[3,1,4,0,2]])
        inv=np.argsort(idx,axis=1)
        torch=SimpleNamespace(float32=np.float32,isfinite=np.isfinite)
        with temporary_order(m,torch,lambda *_:(idx,inv)):
            output=m.forward(x,xyz)
        np.testing.assert_array_equal(seen,[[3,1,4,0,2],[2,0,4,1,3]])
        expected=(((np.arange(5)**2)+np.arange(4,-1,-1)**2)*0.5)[inv[0]]
        np.testing.assert_array_equal(output[0,:,0],x[0,:,0]+expected)

    def test_fallback_and_exception_restore(self):
        m=Mix()
        x=Array(np.zeros((1,5,384),dtype="f4"))
        xyz=Array(np.zeros((1,5,3),dtype="f4"))
        torch=SimpleNamespace(float32=np.float32,isfinite=np.isfinite)
        with self.assertRaisesRegex(RuntimeError,"fixture"):
            with temporary_order(m,torch,lambda *_:None):
                np.testing.assert_array_equal(m.forward(x,xyz),x)
                raise RuntimeError("fixture")
        self.assertEqual(m.calls,2)
        self.assertNotIn("forward",m.__dict__)

    def test_content_changes_invalidate(self):
        x=np.arange(15,dtype="f4").reshape(5,3)
        xyz=x[:3].copy()
        order=np.arange(3)
        frame={"center":[0,1,2],"scale":3}
        key=content_key(x,frame,xyz,order,"geo","v")
        for args in ((x[::-1],frame,xyz,order,"geo","v"),(x,{**frame,"scale":4},xyz,order,"geo","v"),
                     (x,frame,xyz[::-1],order,"geo","v"),(x,frame,xyz,order[::-1],"geo","v"),
                     (x,frame,xyz,order,"geo","w")):
            self.assertNotEqual(key,content_key(*args))

    def test_counts_and_timing_matrix(self):
        rows=schedule(list("ABCDE"),"F",list("ABCDEFGH"))
        self.assertEqual(len(rows),200)
        self.assertEqual(sum(r["phase"]=="batch8" for r in rows),9)
        self.assertEqual(sum(r["phase"] in ("native","forced","manipulation") for r in rows),11)
        for path in ("hot","cold"):
            for arm in "RCS":
                sub=[r for r in rows if (r["kind"],r["arm"])==(path,arm)]
                self.assertEqual(len(sub),30)
                self.assertEqual(sum(r["phase"]=="warmup" for r in sub),5)
                self.assertEqual({c:sum(r["phase"]=="timed" and r["cases"]==[c] for r in sub) for c in "ABCDE"},
                                 dict.fromkeys("ABCDE",5))

    def test_real_thresholds_preserve_failure(self):
        times={k:{a:[20.0]*25 for a in "RCS"} for k in ("hot","cold")}
        peaks={k:{a:100 for a in "RCS"} for k in ("hot","cold","batch8")}
        steps={a:[40.0]*3 for a in "RCS"}
        self.assertTrue(verdict(np,times,peaks,steps)["passed"])
        times["cold"]["S"]=[61.0]*25
        peaks["batch8"]["C"]=111
        r=verdict(np,times,peaks,steps)
        self.assertFalse(r["passed"])
        self.assertFalse(r["gates"]["coldS"])
        self.assertFalse(r["gates"]["allocated_batch8C"])


if __name__=="__main__":
    unittest.main(verbosity=2)
