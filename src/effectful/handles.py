from .core import Effect


def const(value):
    async def const_handle(*a, **kw):
         return value
    return const_handle


def eff(kind, default_handle=None):
    def eff_handle(*a, **kw):
        return Effect(kind, a, kw, default_handle)   
    return eff_handle 

