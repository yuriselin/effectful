from effectful import (
    Effect, effect, 
    resolve_effects,
    map_effects,
    finalize_effects,
    sync_effects,
    compose,
    handles
)


@effect
async def answer():
    return 21


async def scenario():
    return (await answer()) * 2


ctx1 = compose(sync_effects, finalize_effects)

assert ctx1(answer()) == 21
assert ctx1(scenario()) == 42

ctx2 = compose(
    sync_effects,
    finalize_effects,
    map_effects({
        answer: handles.const(44)
    })
)
assert ctx2(scenario()) == 88


@effect(kind="bar")
async def foo(x):
    return x + (await answer())


assert ctx2(foo(10)) == 54


@effect
async def kek():
    x = await answer()
    return await foo(x)

ctx3 = compose(
    sync_effects,
    finalize_effects,
    map_effects({
        "bar": {
            answer: handles.const(2)
        },
        answer: handles.const(40)
    })
)

assert ctx3(kek()) == 42
