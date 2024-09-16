from typing import TYPE_CHECKING, Optional, TypeAlias, Union

from dev_utils.common import get_utc_now

if TYPE_CHECKING:
    from collections.abc import Iterable

    from alembic.operations.ops import MigrationScript
    from alembic.runtime.migration import MigrationContext

    RevisionType: TypeAlias = Union[str, Iterable[Optional[str]], Iterable[str]]  # noqa: UP007


def process_revision_directives_datetime_order(
    context: "MigrationContext",  # noqa: F401
    revision: "RevisionType",  # noqa: F401
    directives: list["MigrationScript"],
) -> None:
    """``process_revision_directives`` function for alembic migration file naming.

    Use in content.configure method:

    https://alembic.sqlalchemy.org/en/latest/api/runtime.html#alembic.runtime.environment.EnvironmentContext.configure
    """
    rev_id = get_utc_now().strftime("%Y%m%d%H%M%S")
    for directive in directives:
        directive.rev_id = rev_id


def process_revision_directives_small_int_order(
    context: "MigrationContext",  # noqa: F401
    revision: "RevisionType",  # noqa: F401
    directives: list["MigrationScript"],
) -> None:
    """``process_revision_directives`` function for alembic migration file naming.

    Use in content.configure method:

    https://alembic.sqlalchemy.org/en/latest/api/runtime.html#alembic.runtime.environment.EnvironmentContext.configure
    """
    migration_script = directives[0]
    head_revision = context.get_current_revision()
    new_rev_id = int(head_revision) + 1 if head_revision else 1
    migration_script.rev_id = f"{new_rev_id:04}"
