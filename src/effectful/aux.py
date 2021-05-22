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


@curry
def map_effects(mapping: t.Mapping, aw: t.Awaitable):
    mapping = {_map_kind(k): v for (k, v) in mapping.items()}
    
    def mapping_handler(eff: Effect):
        handle = mapping.get(eff.kind, None)

        if handle is None:
            return handle

        is_callable = isinstance(handle, t.Callable)
        is_mapping = isinstance(handle, t.Mapping)

        if is_mapping and is_callable:
            raise ValueError(
                "Expected either mapping or callable but "
                "got value implementing both", handle)
        
        if is_mapping:
            return lambda *a, **kw: map_effects(handle, eff.default_handle(*a, **kw))

        if is_callable:
            return handle

        raise ValueError(
            f"Handler mapping should contain either "
            f"another mapping or callable, got {handle}")

    return resolve_effects(mapping_handler, aw)

