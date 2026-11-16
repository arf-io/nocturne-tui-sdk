"""Bounded, complete ownership case partitions; no runtime calls or skips."""
import re
def shard_count(cases):return max(1,(len(cases)+63)//64)
def select_shard(cases,selection=None):
    if selection is None:return cases
    if not isinstance(selection,str) or not re.fullmatch(r'(0|[1-9][0-9]*)/[1-9][0-9]*',selection):raise ValueError('Canonical index/count shard required')
    index,count=map(int,selection.split('/'))
    if not 0<=index<count<=128:raise ValueError('Shard index/count outside range')
    return [case for position,case in enumerate(cases) if position%count==index]
