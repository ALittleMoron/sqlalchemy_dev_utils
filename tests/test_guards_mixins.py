from typing import Any

import pytest

from sqlalchemy_dev_utils import guards
from tests.utils import MyModel


@pytest.mark.parametrize(
    ("test_value", "expected_result"),
    [  # type: ignore[reportUnknownArgumentType]
        (25, False),
        ("string", False),
        (MyModel.id, True),
        (MyModel.full_name, True),  # type: ignore[reportUnknownArgumentType]
    ],
)
def test(test_value: Any, expected_result: bool) -> None:  # noqa: ANN401, FBT001
    assert guards.is_queryable_attribute(test_value) is expected_result
