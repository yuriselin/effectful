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


def mapping_to_handler(
    handles: t.Mapping = _not_passed, /, **extra_handles
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


# TODO split into composition ctx, mapping ctx, etc

class HandlerCtx:
    def __init__(
        self, *ctxs,
        mapping=_not_passed,
        handler=_not_passed,
        handle_all=False, sync=False
    ):
        self._sync = sync
        # sync flag includes handling everything not handled
        self._handle_all = handle_all or sync
        self.handler = None
        self._set_mapping(mapping)
        self._set_handler(handler)
        self._ctxs = tuple()
        self._set_ctx_composition(ctxs)

    def _set_mapping(self, mapping):
        if mapping is _not_passed:
            return
        if not isinstance(mapping, t.Mapping):
            raise TypeError("Not a mapping", mapping)
        self._set_handler(mapping_to_handler(mapping))

    def _set_ctx_composition(self, ctxs):
        if not ctxs:
            return
        # TODO atleast DRY
        traitor = next(
            (c for c in ctxs if not isinstance(c, self.__class__)),
            _not_passed
        )
        if traitor is not _not_passed:
            raise TypeError(
                f"Not an instance of {self.__class__.__name__}", traitor
            )

        traitor = next(
            (c for c in ctxs if c._sync),
            _not_passed
        )
        if traitor is not _not_passed:
            raise TypeError(
                f"Synchronous ctx cant participate in composition", traitor
            )

        self._ctxs = ctxs

    
    def _set_handler(self, handler):
        if handler is _not_passed:
            return

        if not isinstance(handler, t.Callable):
            raise TypeError("Handler is not a callable", handler)
        
        if self.handler is not None:
            raise TypeError(
                "Too many arguments to deduce handler. "
            )

        self.handler = handler

    def __call__(self, aw: t.Awaitable):
        res = aw
        if self.handler is not None:
            res = handle_effects(self.handler, res)
        for c in reversed(self._ctxs):
            res = c(res)
        if self._handle_all:
            res = handle_by_default(res)
        if self._sync:
            res = sync(res)
        return res

    def run(self, f, *args, **kwargs):
        return self(f(*args, **kwargs))

