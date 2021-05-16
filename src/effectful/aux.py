import typing as t
from functools import partial
from decorator import decorator
from .core import (
    Effect, handle_effects,
    EffectHandler, SkipHandling
)


_not_passed = object()


def _map_kind(o):
    try:
        return o.__qualname__
    except AttributeError:
        pass
    return o


def effect(
    default_handle=_not_passed, *,
    kind=_not_passed
):
    @decorator
    def _dec(f, *args, **kw):
        final_kind = kind
        if final_kind is _not_passed:
            final_kind = _map_kind(f)
        
        return Effect(
            kind=final_kind,
            args=args,
            kwargs=kw,
            default_handle=f
        )
    
    if default_handle is _not_passed:
        return _dec

    return _dec(default_handle)


class NotSyncableAwaitable(Exception):
    pass


def sync(aw: t.Awaitable):
    try:
        generated = aw.__await__().send(None)
    except StopIteration as result:
        return result.value
    else:
        raise NotSyncableAwaitable(
            "Awaitable yielded with value", generated)


def default_handler(eff: Effect) -> t.Awaitable:
    return eff.default_handle(*eff.args, **eff.kwargs)


def handle_by_default(aw: t.Awaitable) -> t.Awaitable:
    return handle_effects(default_handler, aw)


def make_handler(
    handles: t.MappingView = _not_passed, /, **extra_handles
) -> EffectHandler:
    handles = dict(handles, **extra_handles)
    handles = {_map_kind(k): v for (k, v) in handles.items()}
    
    async def dict_handler(eff: Effect):
        try:
            handle = handles[eff.kind]
        except KeyError:
            raise SkipHandling
        else:
            return await handle(*eff.args, **eff.kwargs)
    
    return dict_handler

def make_const_handle(value):
    async def const_handle(*a, **kw):
         return value
    return const_handle
