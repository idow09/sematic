# Sematic
from sematic.abstract_future import FutureState
from sematic.db.models.run import Run


def test_set_future_state():
    run = Run()
    run.future_state = FutureState.CREATED
    assert run.future_state == FutureState.CREATED.value


def test_set_description():
    run = Run(description="   abc\n   ")
    assert run.description == "abc"
