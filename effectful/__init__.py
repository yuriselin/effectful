from dataclasses import dataclass
import typing as t

from decorator import decorator


_not_passed = object()


@dataclass
class Effect:
    kind: str
    args: tuple
    kwargs: dict
    default_handle: t.Callable[..., t.Awaitable] = None

    def __post_init__(self):
        if self.default_handle is None:
            self.default_handle = self._not_implemented_handle

    def _not_implemented_handle(self, *args, **kwargs):
        raise NotImplementedError(
            "Performed effect with no handler", self
        )

    def __await__(self):
        yield self


EffectHandler = t.Callable[[Effect], t.Awaitable]


def perform_generator(
    handler: EffectHandler,
    gen: t.Generator
) -> t.Generator:
    send, throw = None, None
    while True:
        try:
            mb_effect = gen.throw(throw) if throw is None else gen.send(send)
        except StopIteration as result:
            return result.value
        else:
            send, throw = None, None
            try:
                if isinstance(mb_effect, Effect):
                    subgen = handler(mb_effect).__await__()
                    send = yield from perform_generator(handler, subgen)
                else:
                    send = yield mb_effect
            except Exception as e:
                throw = e
            continue


class _Coroutine:
    __slots__ = ["gen"]

    def __init__(self, gen: t.Generator):
        self.gen = gen
    
    def __await__(self):
        return self.gen


def perform_awaitable(
    handler: EffectHandler, aw: t.Awaitable
) -> t.Awaitable:
    return _Coroutine(
        perform_generator(handler, aw.__await__())
    )


def _map_kind(o):
    try:
        return o.__qualname__
    except AttributeError:
        pass
    raise NotImplementedError


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
