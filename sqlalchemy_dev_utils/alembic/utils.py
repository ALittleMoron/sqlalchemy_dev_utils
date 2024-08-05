from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from alembic.config import Config


def get_config_variable_as_list(
    config: "Config",
    key: str,
    section: str | None = None,
) -> list[str]:
    """Parse alembic.ini file for given key as list of strings.

    Parameters
    ----------
    config
        object of alembic config.
    key
        name of variable in alembic.ini config.
    section
        name of ini file section (default None will be replaced with main section - [alembic] or
        your custom, if you change it in config).

    Returns
    -------
    list[str]
        parsed segment as list of None.
    """
    if section is None:
        section = config.config_ini_section
    if (arr := config.get_section_option(section, key)) is None:
        return []
    return [token for a in arr.split("\n") for b in a.split(",") if (token := b.strip())]
