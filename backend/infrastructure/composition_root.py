
# Composition root.

# This is the one place where concrete Infrastructure implementations
# get wired to the abstract Ports defined in domain/ports. Application
# and Domain code never see this file — they only ever see the Ports.
# This file is intentionally near-empty right now. Real bindings get
# added once repository and LLM provider implementations exist.

from application.container import container


def bootstrap():
    #Called once when Django starts. Registers all bindings.
    pass