from dataclasses import dataclass
import typing as t
from toolz import curry


GenYield = t.TypeVar("GenYield")
GenSend = t.TypeVar("GenSend")
GenReturn = t.TypeVar("GenReturn")
MitmYield = t.TypeVar("MitmYield")
MitmSend = t.TypeVar("MitmSend")


def mitm_generator(
    mitm: t.Callable[[GenYield], t.Generator[MitmYield, MitmSend, GenSend]],
    gen: t.Generator[GenYield, GenSend, GenReturn]
) -> t.Generator[MitmYield, MitmSend, GenReturn]:
    """
    Transforms everything 'gen' yields and takes as an input.

    For every item 'gen' yields 'mitm' call initializes
    another generator which result or exception sends back to 'gen'
    and everything this generator yields in its place proxing through
    resulting gen.
    """
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


EffectHandle = t.Callable[..., t.Awaitable]

@dataclass
class Effect:
    kind: str
    args: tuple
    kwargs: dict
    default_handle: EffectHandle = None

    def __post_init__(self):
        if self.default_handle is None:
            self.default_handle = self._not_implemented_handle

    def _not_implemented_handle(self, *args, **kwargs):
        raise NotImplementedError(
            "Performed effect with no handler", self
        )

    def __await__(self):
        handle = (yield self)
        result = yield from handle(*self.args, **self.kwargs).__await__()
        return result

    def call_default(self):
        return self.default_handle(*self.args, **self.kwargs)


EffectHandler = t.Callable[[Effect], t.Optional[EffectHandle]]


def resolve_effects_generator(
    handler: EffectHandler,
    gen: t.Generator
) -> t.Generator:
    def handle_effect(mb_effect):
        if isinstance(mb_effect, Effect):
            handle = handler(mb_effect)
            if handle is not None:
                return handle
        return (yield mb_effect)
    
    return mitm_generator(handle_effect, gen)


class _Coroutine:
    __slots__ = ["gen"]

    def __init__(self, gen: t.Generator):
        self.gen = gen
    
    def __await__(self):
        return self.gen


def resolve_effects_awaitable(
    handler: EffectHandler, aw: t.Awaitable
) -> t.Awaitable:
    return _Coroutine(
        resolve_effects_generator(handler, aw.__await__())
    )


resolve_effects = curry(resolve_effects_awaitable)