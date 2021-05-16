
from functools import partial
from effectful import (
    Effect, handle_effects,
    effect, sync, handle_by_default,
    compose, make_const_handle,
    make_handler, handle_effects
)


@effect
async def answer():
    return 21


async def scenario():
    return (await answer()) * 2


performer = compose(sync, handle_by_default)
assert performer(scenario()) == 42


answer_handler = make_handler({
    answer: make_const_handle(44)
})

performer = compose(performer, partial(handle_effects, answer_handler))

assert performer(scenario()) == 88