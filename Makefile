PYTEST=pytest -q

.PHONY: test test-unit test-smoke

test: test-unit

test-unit:
	$(PYTEST) tests/unit

test-smoke:
	$(PYTEST) tests/smoke

