import pytest

from effectful import (
    Effect, handle_effects,
    effect, sync, handle_by_default,
    compose
)


@effect
async def answer():
    return 21


async def scenario():
    return (await answer()) * 2


def test_basic():
    performer = compose(sync, handle_by_default)
    performer(scenario())
