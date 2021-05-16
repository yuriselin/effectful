from dataclasses import dataclass
import typing as t


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
        return (yield self)


EffectHandler = t.Callable[[Effect], t.Awaitable]


def _mitm_generator(
    mitm: t.Generator,
    gen: t.Generator
) -> t.Generator:
    send, throw = None, None
    while True:
        try:
            generated = gen.throw(throw) \
                if throw is not None \
                else gen.send(send)
        except StopIteration as result:
            return result.value
        else:
            send, throw = None, None
            try:
                send = yield from mitm(generated)
            except Exception as e:
                throw = e


class SkipHandling(Exception):
    pass


def handle_effectful_generator(
    handler: EffectHandler,
    gen: t.Generator,
    shallow: bool = False
) -> t.Generator:
    def handle_effect(mb_effect):
        if isinstance(mb_effect, Effect):
            subgen = handler(mb_effect).__await__()
            if not shallow:
                subgen = _mitm_generator(handle_effect, subgen)
            try:
                result = yield from subgen
                return result
            except SkipHandling:
                pass
        return (yield mb_effect)
    
    return _mitm_generator(handle_effect, gen)


class _Coroutine:
    __slots__ = ["gen"]

    def __init__(self, gen: t.Generator):
        self.gen = gen
    
    def __await__(self):
        return self.gen


def handle_effectful_awaitable(
    handler: EffectHandler, aw: t.Awaitable
) -> t.Awaitable:
    return _Coroutine(
        handle_effectful_generator(handler, aw.__await__())
    )


handle_effects = handle_effectful_awaitable