.PHONY: build check new clean help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

build: ## Generate _sync/ YAML from transforms/
	python3 scripts/build.py

check: ## Verify _sync/ is up to date (for CI)
	python3 scripts/build.py --check

new: ## Create a new transform: make new domain=revenue name=monthly_arr
	@if [ -z "$(domain)" ] || [ -z "$(name)" ]; then \
		echo "Usage: make new domain=revenue name=monthly_arr"; \
		exit 1; \
	fi
	@mkdir -p transforms/$(domain)
	@cp transforms/_template.sql transforms/$(domain)/$(name).sql
	@cp transforms/_template.meta.yml transforms/$(domain)/$(name).meta.yml
	@sed -i 's/my_transform/$(name)/g' transforms/$(domain)/$(name).meta.yml
	@echo "Created:"
	@echo "  transforms/$(domain)/$(name).sql"
	@echo "  transforms/$(domain)/$(name).meta.yml"
	@echo ""
	@echo "Next: edit the SQL and metadata, then run 'make build'"

clean: ## Remove generated _sync/ directory
	rm -rf _sync/

lint: ## Check SQL files for common issues
	@echo "Checking for trailing whitespace in SQL files..."
	@find transforms -name '*.sql' ! -name '_*' -exec grep -ln ' $$' {} \; | \
		while read f; do echo "  WARN: trailing whitespace in $$f"; done || true
	@echo "Checking for missing .meta.yml companions..."
	@find transforms -name '*.sql' ! -name '_*' | while read f; do \
		meta="$${f%.sql}.meta.yml"; \
		if [ ! -f "$$meta" ]; then echo "  WARN: missing $$meta"; fi; \
	done
	@echo "Lint complete."
