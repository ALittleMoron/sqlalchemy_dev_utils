
# SQLAlchemy Dev utils

![coverage](./coverage.svg)

## For what?

I made this project to avoid copy-pasting with utils in my projects. I was aiming to simplify
working with sqlalchemy.

See sources for more info about utils. README (or probably, separated documentation), will be
updated soon.

## Install

With pip:

```bash
pip install sqlalchemy-dev-utils
```

With pdm:

```bash
pdm add sqlalchemy-dev-utils
```

With poetry:

```bash
poetry add sqlalchemy-dev-utils
```

Package has optional dependencies, so if you use it in some specific cases, install only needed
dependencies.

For alembic utils:

```bash
pip install "sqlalchemy-dev-utils[alembic]"
```

For pydantic model field:

```bash
pip install "sqlalchemy-dev-utils[pydantic_field]"
```

For relativedelta model field (replace for timedelta):

```bash
pip install "sqlalchemy-dev-utils[relativedelta_field]"
```
