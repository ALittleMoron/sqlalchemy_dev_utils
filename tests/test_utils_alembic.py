from typing import Any
from unittest.mock import Mock

import pytest

from sqlalchemy_dev_utils.alembic import utils as alembic_utils


@pytest.mark.parametrize(
    ('mock_value', 'key', 'section', 'expected_result'),
    [
        ("abc, dce, aboba", "excluded", None, ["abc", "dce", "aboba"]),
        ("abc, dce, aboba", "excluded", "some_other", ["abc", "dce", "aboba"]),
        (None, 'some_key', None, []),
    ],
)
def test(
    mock_value: str | None,
    key: str,
    section: str | None,
    expected_result: list[Any],
) -> None:
    config = Mock()
    config.config_ini_section = "[alembic]"
    config.get_section_option.return_value = mock_value
    assert alembic_utils.get_config_variable_as_list(config, key, section) == expected_result
