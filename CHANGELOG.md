# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- **httpx 0.28 compatibility**: `Session.create()` now passes `app` via `transport=ASGITransport(app=...)` (async) and `transport=WSGITransport(app=...)` (sync) instead of the removed `app=` keyword argument. No transport is set when `app` is `None` (real HTTP calls).

## [1.0.0] - 2026-03-16

### Added
- `converter.py` — new `cattrs`-based converter module with custom structure/unstructure hooks for `Namespace`, `UUID`, and `io.BufferedReader`
- `mapping_field()` utility in `converter.py` to replicate `related.MappingField` behavior using attrs/cattrs
- Semaphore regression test (`tests/wsgi/semaphore.rigor`) verifying semaphores work correctly across multiple `execute()` calls

### Changed
- **Migrated `model.py`, `config.py`, `session.py`, `state.py`, `swagger.py`, and `reporting.py` from `related` to `attrs`/`cattrs`** — the `related` library is no longer a dependency for any core module
- `Session` and `AsyncSession` in `session.py` converted from `@related.immutable` to `@attrs.frozen`
- `State`, `StepState`, `StepResult`, `ScenarioResult` in `state.py` converted from `@related.mutable` to `@attrs.define(slots=False)` to support `Timer` context manager dynamic attributes
- `ValidationResult`, `Fetch`, `CaseResult`, `SuiteResult` in `state.py` converted from `@related.immutable` to `@attrs.frozen`
- `Swagger`, `Path`, `Operation`, `Parameter`, `Definition` and supporting classes in `swagger.py` converted from `@related.mutable` to `@attrs.define` with cattrs structure hooks for field key aliases (`is_in`/`"in"`, `is_not`/`"not"`)
- `Swagger.loads()` now uses `yaml.safe_load` + `converter.structure` instead of `related.from_yaml` + `related.to_model`
- `DocString.section()` in `reporting.py` now uses `converter.unstructure` instead of `related.to_dict` for serializing step results
- `generate_json()` in `reporting.py` now uses `converter.unstructure` before `json.dumps`
- Request body serialization in `Fetch.get_kwargs()` now uses `json.dumps(data, default=str)` for both `dict` and `list` bodies, replacing `related.to_json`
- `related.to_model(enums.Comparison, compare)` replaced with `enums.Comparison(compare)` in `State.check_validation()`
- Status validator in `State.do_validate()` now correctly passes `enums.Comparison.IN.value` (string `"in"`) rather than the enum object, preventing `!!python/object/apply` tags in YAML output
- `asyncio.get_event_loop()` replaced with `asyncio.new_event_loop()` + `asyncio.set_event_loop()` in `collect.py` and `session.py` for compatibility with Python 3.12+
- `asyncio.ensure_future()` + `run_until_complete()` pattern replaced with direct `loop.run_until_complete(coroutine)` in `collect.py` and `session.py`, removing dependency on a running loop for task scheduling
- `AsyncSession.loop` type annotation changed from `object` to `asyncio.AbstractEventLoop`
- `AsyncSession.run()` now recreates semaphores bound to the current event loop before each run, fixing `RuntimeError: Semaphore is bound to a different event loop` on Python 3.12+ when retrying failed scenarios
- `--extensions` CLI flag short form changed from `-e` to `-x` to resolve conflict with `--excludes` (`-e`)
- Switched from `setup.py`/`Pipfile` to `pyproject.toml` and `uv`  with `requirements.txt` for dependency management

### Fixed
- `Case.loads()` error recovery now correctly returns an invalid `Case` instead of re-raising the exception
- `Requestor` structure hook now handles bare string shorthand (`request: /path`) in `.rigor` files
- `Iterator` structure hook prevents `Namespace` hook from being incorrectly applied to `Iterator` subclass
- List request bodies were not being JSON-serialized before being sent, causing 500 errors on endpoints expecting a JSON array
- `Comparison` enum stored in `Validator.compare` (typed `str`) was serialized as a Python object tag in YAML debug output

### Removed
- `related` library dependency removed from all source modules
- `setup.py`, `Pipfile`, `Pipfile.lock`, `tox.ini`, `.travis.yml`, `travis_pypi_setup.py` removed in favour of `pyproject.toml`

## [0.7.5] - 2024-08-13

### Changed
- Updated Python version and dependencies
- Replaced `setup.py` and `Pipfile` with `pyproject.toml`
- Moved `tox.ini` configuration into `pyproject.toml`
- Removed Travis CI in favour of consolidated build configuration

## [0.7.4] - 2024-01-01

### Fixed
- Retained comments in tables during `process_reformat`

## [0.7.3] - 2023-01-01

### Changed
- Loosened Click version requirements
