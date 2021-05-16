
from functools import partial
from effectful import (
    Effect, effect, 
    make_const_handle,
    HandlerCtx
)


@effect
async def answer():
    return 21


async def scenario():
    return (await answer()) * 2


ctx = HandlerCtx(sync=True)
assert ctx(answer()) == 21
assert ctx(scenario()) == 42

ctx2 = HandlerCtx(HandlerCtx(mapping={
    answer: make_const_handle(44)
}), sync=True)
assert ctx2(scenario()) == 88


@effect(kind="bar")
async def foo(x):
    return x + (await answer())

assert ctx(foo(10)) == 31

ctx2 = HandlerCtx(HandlerCtx(mapping={
    answer: make_const_handle(44)
}), sync=True)
# performer_x = compose(performer, partial(handle_effects, answer_handler))
