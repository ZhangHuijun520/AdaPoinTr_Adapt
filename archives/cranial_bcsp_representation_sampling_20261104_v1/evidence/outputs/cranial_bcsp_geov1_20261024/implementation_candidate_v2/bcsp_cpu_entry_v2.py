"""Isolated CPU integration candidate, not a production training launcher."""
import ast
import hashlib
import importlib.util
import sys
from pathlib import Path
import torch
from torch.utils.data import Dataset, DataLoader

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
V1 = BASE.parent / 'implementation_candidate_v1' / 'bcsp_adapter.py'
PARENT = ROOT / 'outputs/cranial_scqr_v12_qa_github_publish_20261019/models/Transformer_utils.py'
PARENT_SHA = '44d4aaabf9cbb09a4b7b9b4c1518b7901481a28304502508962b2e2d1082d289'
V1_SHA = '2f7d3050cfb6ac2602cc17a95b860da2204daef2dfa63dab63d233e899b7dd55'

def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load_adapter():
    if _sha(V1) != V1_SHA:
        raise RuntimeError('v1 adapter drift')
    name = '_bcsp_frozen_adapter_v1'
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, V1)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        try:
            spec.loader.exec_module(module)
        except BaseException:
            del sys.modules[name]
            raise
    return sys.modules[name]

def parent_knn_pair():
    """Load only two hash-bound function ASTs; never import the model tree."""
    if _sha(PARENT) != PARENT_SHA:
        raise RuntimeError('parent KNN source drift')
    source = ast.parse(PARENT.read_text(encoding='utf8'))
    functions = [n for n in source.body if isinstance(n, ast.FunctionDef)
                 and n.name in {'knn_point', 'square_distance'}]
    if len(functions) != 2:
        raise RuntimeError('parent function contract changed')
    namespace = {'torch': torch}
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(PARENT), 'exec'), namespace)
    return namespace['knn_point'], namespace['square_distance']

def candidate_knn(k, xyz, query, chunk=256):
    if xyz.device.type != 'cpu' or query.device.type != 'cpu':
        raise ValueError('this validation entry is CPU-only')
    # Direct dispatch, not ContextVar propagation through DataParallel threads.
    return load_adapter().torch_knn(k, xyz, query, chunk)

class BCSPDataset(Dataset):
    """Registration-ready explicit dataset API; no global legacy registry edits."""
    def __init__(self, root, records, allowed_sources, n_input, training):
        self.root = Path(root)
        self.records = tuple(dict(r) for r in records)
        self.allowed_sources = frozenset(allowed_sources)
        self.n_input = n_input
        self.training = bool(training)
        ids = [r.get('case_id') for r in self.records]
        if not ids or any(not isinstance(i, str) or not i for i in ids) or len(ids) != len(set(ids)):
            raise ValueError('unique nonempty case IDs required')
        if any(r.get('source_id') not in self.allowed_sources for r in self.records):
            raise ValueError('source outside explicit fold')
    def __len__(self):
        return len(self.records)
    def __getitem__(self, index):
        partial, target = load_adapter().load_case(
            self.root, self.records[index], self.allowed_sources, self.n_input,
            training=self.training)
        partial = torch.from_numpy(partial)
        return (partial, torch.from_numpy(target)) if self.training else partial

def build_cpu_loader(dataset, epoch, seed=0):
    if not dataset.training or len(dataset) != 315:
        raise ValueError('315-case explicit training dataset required')
    if type(epoch) is not int or not 0 <= epoch < 100:
        raise ValueError('epoch labels must be 0..99')
    if seed != 0:
        raise ValueError('only bound seed0 allowed')
    generator = torch.Generator(device='cpu').manual_seed(seed + epoch)
    return DataLoader(dataset, batch_size=8, drop_last=True, shuffle=True,
                      num_workers=0, generator=generator)

def run_cpu_epoch(dataset, epoch, optimizer, compute_gradients, guard):
    """Trusted callback supplies loss/backward/clip; no models constructed here."""
    loader = build_cpu_loader(dataset, epoch)
    if len(loader) != 39:
        raise RuntimeError('loader count mismatch')
    def callback(partial, target):
        if partial.device.type != 'cpu' or target.device.type != 'cpu':
            raise ValueError('CPU-only tensors required')
        if partial.shape != (8, dataset.n_input, 3) or target.shape != (8, 8192, 3):
            raise ValueError('batch shape mismatch')
        compute_gradients(partial, target)
    load_adapter().run_epoch(loader, epoch, optimizer, callback, guard)

def finish_cpu_contract(guard):
    result = guard.finish()
    result['status'] = 'CPU_CONTRACT_ONLY_NOT_TRAINING_AUTHORIZATION'
    return result
