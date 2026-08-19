"""Hermes directory-plugin entry point."""

try:
    # Hermes directory plugins are loaded as a namespaced package; prefer the
    # sibling package without requiring the checkout root on sys.path.
    from .adaptive_evolution_observer import register
except ImportError:
    # Direct checkout/import fallback and editable-install compatibility.
    from adaptive_evolution_observer import register

__all__ = ["register"]
