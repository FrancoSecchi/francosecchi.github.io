# Local preview for the Jekyll blog. GitHub Pages builds the published site on its own.
RUBY_VERSION ?= 3.1.2
PORT ?= 4000
JEKYLL = RBENV_VERSION=$(RUBY_VERSION) bundle exec jekyll

.PHONY: help install serve serve-published build clean

help: ## List available commands
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F ':.*## ' '{printf "  make %-16s %s\n", $$1, $$2}'

install: ## Install Jekyll and the GitHub Pages gems into vendor/
	RBENV_VERSION=$(RUBY_VERSION) bundle config set --local path vendor/bundle
	RBENV_VERSION=$(RUBY_VERSION) bundle install

serve: ## Serve locally with drafts and live reload (http://localhost:4000)
	$(JEKYLL) serve --drafts --livereload --port $(PORT)

serve-published: ## Serve locally exactly as it will be published (no drafts)
	$(JEKYLL) serve --livereload --port $(PORT)

build: ## Build the site into _site/
	$(JEKYLL) build

clean: ## Remove generated files
	rm -rf _site .jekyll-cache .jekyll-metadata
