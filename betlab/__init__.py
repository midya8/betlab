"""Auditable exact-rational sequential evidence for bounded paired scores."""
from .core import replay, paired
from .tree import audit_tree, coin_tree
from .demo import demo
from .starts import start_mixture, audit_starts, starts_demo
__version__ = '0.3.0'
__all__ = ['replay', 'paired', 'audit_tree', 'coin_tree', 'demo', 'start_mixture', 'audit_starts', 'starts_demo']

from .confidence import mean_evidence, confidence_sequence, confidence_demo
__all__ += ['mean_evidence', 'confidence_sequence', 'confidence_demo']
