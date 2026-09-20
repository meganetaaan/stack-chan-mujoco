"""Explicit, incompatible R6 observation versions; never guess from dimensions."""
from .residual import ResidualEnv
from .residual_heading import HeadingResidualEnv


def make_env(config,**kwargs):
    if config['schema']=='r6-residual-v1':return ResidualEnv(config,**kwargs)
    if config['schema']=='r6-residual-heading-v2':return HeadingResidualEnv(config,**kwargs)
    raise ValueError('unknown R6 environment schema')
