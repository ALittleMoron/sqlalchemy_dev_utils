from unittest.mock import Mock

import pytest

from sqlalchemy_dev_utils.alembic.ignore_table import build_include_object_function


@pytest.mark.parametrize(
    ('mock_value', 'key', 'section', 'include_name', 'include_type', 'expected_result'),
    [
        (
            "abc, dce, aboba",
            "excluded",
            None,
            'abc',
            'table',
            False,
        ),
        (
            "abc, dce, aboba",
            "excluded",
            "some_other",
            'dce',
            'schema',
            True,
        ),
        (
            "abc, dce, aboba",
            "excluded",
            "some_other",
            'table',
            'aastast',
            True,
        ),
    ],
)
def test_build_include_object_function(  # noqa: PLR0913
    mock_value: str | None,
    key: str,
    section: str | None,
    include_name: str,
    include_type: str,
    expected_result: bool,  # noqa: FBT001
) -> None:
    config = Mock()
    config.config_ini_section = "[alembic]"
    config.get_section_option.return_value = mock_value
    include_object = build_include_object_function(config, key, section)
    assert callable(include_object)
    assert include_object(None, include_name, include_type, True, None) is expected_result  # type: ignore[reportArgumentType]  # noqa: FBT003
