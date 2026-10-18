# Testing

The project ships with a pytest suite for the backend and the bot's
command formatters. Run everything with `make test`.

## Backend

```bash
cd backend
pip install -r requirements-dev.txt
CHECKER_ENABLED=false python -m pytest tests/ -q
```

`CHECKER_ENABLED=false` stops the background checker thread so tests run
deterministically. The conftest redirects the database to a temporary
SQLite file and resets tables between tests.

### Coverage

```bash
cd backend
CHECKER_ENABLED=false python -m pytest tests/ --cov=app --cov-report=term-missing
```

The CI workflow runs coverage and fails if it drops below the configured
threshold in `pyproject.toml`.

### What the tests cover

| Area | File |
| --- | --- |
| Product API (upsert, list, history, delete) | `tests/test_products_api.py` |
| Archive/restore endpoints | `tests/test_archive.py` |
| Prune endpoint | `tests/test_pruning.py` |
| Stats and notes | `tests/test_stats_notes.py` |
| Summary endpoint | `tests/test_summary.py` |
| Notification cooldown | `tests/test_cooldown.py` |
| Rate limiting & security middleware | `tests/test_security_rate.py` |
| API response contracts | `tests/test_api_contract.py` |
| Input validation | `tests/test_validation.py` |
| Background checker | `tests/test_checker.py` |
| Export helpers | `tests/test_export_unit.py`, `tests/test_export_extended.py` |
| Filters service | `tests/test_filters_unit.py` |
| Targets service | `tests/test_targets_unit.py` |
| Dedupe service | `tests/test_dedupe_unit.py` |
| Archive service | `tests/test_archive_unit.py` |
| Health service | `tests/test_health_unit.py` |
| Logging config | `tests/test_logging_unit.py` |
| Notifier retry/backoff | `tests/test_notifier_retry.py` |
| History limit param | `tests/test_history_limit.py` |

## Bot

```bash
cd bot
python -m pytest test_commands.py test_state.py -q
```

These cover the pure command formatters (`cmd_list`, `cmd_stats`,
`cmd_top`, `cmd_recent`, `cmd_settings`, `parse_target_arg`) and the
per-chat alert state store.

## Extension & dashboard

The extension and dashboard are plain JavaScript without a test runner.
Validate syntax locally:

```bash
node --check extension/background.js
node --check extension/popup/popup.js
node --check web/app.js
```

Manual test checklist:

1. Start the backend, open the dashboard at `http://localhost:8000/dashboard`.
2. Load the unpacked extension, track a product on Shopee/TikTok.
3. Set a target price and confirm the popup badge + notification.
4. Toggle theme/filters/sorting and confirm state persists.
