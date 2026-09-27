# Development

Library: Python >=3.13. Integration tests: Python >=3.14.2 on Linux, with HA 2026.9.4.
Windows can run the independent library suite. The upstream HA test harness imports
POSIX `fcntl`; do not fake that module to claim a Windows integration-test pass.

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[test,dev]'
python -m pip install -r requirements-ha-test.txt
python scripts/sync_vendor.py
ruff check .
ruff format --check .
mypy
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -p pytest_asyncio.plugin -p pytest_cov tests/test_library.py tests/test_transport.py tests/test_metadata.py --cov=pyhaassohn --cov-report=term-missing
pytest tests/integration --cov=custom_components.haassohn --cov-report=term-missing
python -m build
python scripts/package_integration.py
```

On PowerShell activate `.venv\Scripts\Activate.ps1`. Keep the separate HA testing
environment on Linux; HA Container does not require a separate daemon for the
integration. Docker, if used for development tests, is test infrastructure only.

`tests/emulator.py` runs a loopback-only synthetic aiohttp server for HSP2/6/7/8 and
Hark profiles. It independently implements authentication, command rejection and
readback and keeps an ordered request trace. Fault injection tests cover HTTP
errors, partial/disconnected responses, size limits, timeouts and cancellation.
It never connects to a real stove. Test-only PINs and serials are explicitly synthetic.

For a release, set actual repository metadata with `scripts/configure_repository.py`,
run all gates including Linux HA tests, and run the manual release workflow. That
workflow builds downloadable artifacts; it never publishes to PyPI automatically.
Do not claim HACS default-store listing or HA Core approval based on this scaffold.
