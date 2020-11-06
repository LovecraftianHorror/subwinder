## Contributing to `subwinder`

If you want to help with the development of `subwinder` then feel free to pick up on any of the issues listed. If you would like to contribute a new feature or modify existing behavior then please raise an issue first to discuss the changes.

### Style Guidelines

This library uses `black`, `flake8`, `isort`, and `mypy` to lint and format code and for this reason these are all listed under the `tool.poetry.dev-dependencies` in the `pyproject.toml`. Please ensure any code contributed follows both of these (there are some incompatible rules between them that are ignored in either the `.flake8` file or under `tool.black` and `tool.isort` in the `pyproject.toml`).

After making changes running `flake8 .`, `black .`, `isort --atomic .`, and `mypy .` in the root of the repo should be enough to automatically format and make changes or nag. Testing with `pytest` will also flag if any of these are not up to date, so running the test suite should be enough to notice any problems.

### Tests

Unit testing is done with the help of `pytest` (also one of the `dev-dependencies`). Make sure any changes you contribute pass the test suite, or fix the issue if the test suite is inaccurate. Preferably any new features should include tests to ensure the behavior is correct.

## Tools

If you run into wanting to generate fake files to use with `Media` then you can look under the `dev` directory where `fake_media.py` can help you.
