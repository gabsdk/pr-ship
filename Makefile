PREFIX ?= $(shell bash lib/pr-ship/install-paths.sh)
BINDIR = $(PREFIX)/bin
SHAREDIR = $(PREFIX)/share/pr-ship
LANGDIR = $(SHAREDIR)/lang

.PHONY: build install uninstall test

build:

install:
	install -d "$(DESTDIR)$(BINDIR)"
	install -d "$(DESTDIR)$(LANGDIR)"
	install -m 755 bin/pr-ship "$(DESTDIR)$(BINDIR)/pr-ship"
	install -m 644 lib/pr-ship/ui.sh "$(DESTDIR)$(SHAREDIR)/ui.sh"
	install -m 644 lib/pr-ship/lang/*.sh "$(DESTDIR)$(LANGDIR)/"

uninstall:
	rm -f "$(DESTDIR)$(BINDIR)/pr-ship"
	rm -rf "$(DESTDIR)$(SHAREDIR)"

test:
	PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
