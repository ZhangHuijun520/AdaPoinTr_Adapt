"""Per-instance, read-only SPCG observation. No torch import or model execution on import."""
import ast
import hashlib
import types
from pathlib import Path

HEAD_SHA = '687c123ae7d0769c9ee89e2067367ff7fc2762f66bf47a814bf077ac68c59d3b'
SCORE_EXPR = 'delta.detach().square().sum(-1)'

def need(ok, message):
    if not ok:
        raise ValueError(message)

class Observer:
    def __init__(self, head, source, torch):
        self.h, self.t, self.source = head, torch, Path(source)
        self.hook = None
        self.opened = False

    def __enter__(self):
        h = self.h
        raw = self.source.read_bytes()
        need(hashlib.sha256(raw).hexdigest() == HEAD_SHA, 'frozen head bytes')
        need(h.arm in ('G1', 'G2') and h.net[0].in_features == 1416, 'actual head interface')
        need(not hasattr(h, '_trace_scores'), 'observer already attached')
        self.saved = (h.capture, h.last, h.last_q, h.__dict__.get('describe'))
        try:
            if h.arm == 'G2':
                cls = next(n for n in ast.parse(raw).body if isinstance(n, ast.ClassDef) and n.name == 'SPCGHead')
                method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'describe')
                matches = [n for n in ast.walk(method) if isinstance(n, ast.Call) and ast.unparse(n.func) == 'torch.argsort']
                need(len(matches) == 1 and ast.unparse(matches[0].args[0]) == SCORE_EXPR, 'one exact native score consumer')
                matches[0].args[0] = ast.copy_location(ast.Call(func=ast.Attribute(value=ast.Name(id='self', ctx=ast.Load()), attr='_trace_scores', ctx=ast.Load()), args=[matches[0].args[0]], keywords=[]), matches[0].args[0])
                env = dict(h.describe.__func__.__globals__)
                module = ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[]))
                exec(compile(module, str(self.source), 'exec', dont_inherit=True), env)
                h.describe = types.MethodType(env['describe'], h)
                h._trace_scores = self.scores
            self.hook = h.net[0].register_forward_pre_hook(self.head_input)
            h.capture = True
            self.opened = True
            self.begin()
            return self
        except BaseException:
            self.close()
            raise

    def begin(self):
        need(self.opened, 'observer not open')
        self.x = self.d2 = None
        self.x_calls = self.score_calls = 0
        self.h.last = self.h.last_q = None

    def scores(self, score):
        self.score_calls += 1
        need(self.score_calls == 1, 'one score consumer per full forward')
        self.d2 = score.detach().clone()
        return score  # The same object is consumed by the original argsort.

    def head_input(self, module, args):
        self.x_calls += 1
        need(len(args) == 1 and self.x_calls == 1, 'one real H input')
        self.x = args[0].detach().clone()
        return None

    def finish(self, D, Q, P):
        t, h = self.t, self.h
        need(self.x_calls == 1 and self.score_calls == (1 if h.arm == 'G2' else 0), 'same-forward observation counts')
        need(h.last is not None and t.equal(h.last_q, Q), 'head Q is returned native coarse')
        values = dict(D=D, Q=Q, P=P, x=self.x, f=self.x[..., 1024:1408], **h.last)
        index = values.pop('index')
        shapes = dict(D=(8192,3), S=(256,3), F=(256,384), z=(1024,), A=(256,3), x=(256,1416), f=(256,384), mu=(256,3), rho=(256,1), tau=(256,1), Q=(256,3), P=(8192,3))
        need(set(values) == set(shapes), 'exact captured fields')
        for k, shape in shapes.items():
            v = values[k]
            need(tuple(v.shape) == (1, *shape) and v.dtype == t.float32 and bool(t.isfinite(v).all()), 'finite FP32 ' + k)
        need(t.equal(self.x[..., :1024], values['z'][:, None].expand(-1,256,-1)), 'actual z segment')
        for key, lo, hi in [('A',1408,1411),('mu',1411,1414),('rho',1414,1415),('tau',1415,1416)]:
            need(t.equal(self.x[..., lo:hi], values[key]), 'actual x segment ' + key)
        if h.arm == 'G2':
            need(index is not None and tuple(index.shape) == (1,256,8) and index.dtype == t.int64, 'actual k8 index')
            need(tuple(self.d2.shape) == (1,256,256) and self.d2.dtype == t.float32 and bool(t.isfinite(self.d2).all()), 'actual FP32 score')
            values.update(index=index, native_d2=self.d2)
        else:
            need(index is None and self.d2 is None, 'G1 ALL256, no fake k8')
        return {k:v.detach().cpu().contiguous().numpy()[0].copy() for k,v in values.items()}

    def close(self):
        if self.hook is not None:
            self.hook.remove()
            self.hook = None
        if hasattr(self, 'saved'):
            capture, last, q, describe = self.saved
            self.h.capture, self.h.last, self.h.last_q = capture, last, q
            if describe is None:
                self.h.__dict__.pop('describe', None)
            else:
                self.h.describe = describe
            self.h.__dict__.pop('_trace_scores', None)
        self.opened = False
        self.x = self.d2 = None

    def __exit__(self, *exc):
        self.close()
