import typing as t
from decorator import decorator
from .core import (
    Effect, resolve_effects,
    EffectHandler, EffectHandle
)
from toolz import curry


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


def sync_effects(aw: t.Awaitable):
    try:
        generated = aw.__await__().send(None)
    except StopIteration as result:
        return result.value
    else:
        raise NotSyncableAwaitable(
            "Awaitable yielded with value", generated)


def finalize_effects(aw: t.Awaitable):
    def defaults_handler(eff: Effect):
        return eff.default_handle

    return resolve_effects(defaults_handler, aw)


def _mapping_to_handler(
    handles: t.Mapping = _not_passed, /, **extra_handles
) -> EffectHandler:
    handles = dict(handles, **extra_handles)
    handles = {_map_kind(k): v for (k, v) in handles.items()}
    
    def map_handler(eff: Effect):
        return handles.get(eff.kind, None)
    
    return map_handler


@curry
def map_effects(mapping: t.Mapping, aw: t.Awaitable):
    return resolve_effects(_mapping_to_handler(mapping), aw)

