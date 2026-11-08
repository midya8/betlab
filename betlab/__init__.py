"""Auditable exact-rational sequential evidence for bounded paired scores."""
from .core import replay, paired
from .tree import audit_tree, coin_tree
from .demo import demo
__version__ = '0.1.0'
__all__ = ['replay', 'paired', 'audit_tree', 'coin_tree', 'demo']
