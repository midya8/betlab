"""Auditable exact-rational sequential evidence for bounded paired scores."""
from .core import replay, paired
from .tree import audit_tree, coin_tree
from .demo import demo
from .starts import start_mixture, audit_starts, starts_demo
__version__ = '0.2.0'
__all__ = ['replay', 'paired', 'audit_tree', 'coin_tree', 'demo', 'start_mixture', 'audit_starts', 'starts_demo']
