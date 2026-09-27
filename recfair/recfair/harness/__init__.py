"""Runtime harness for the resilient architecture (E4).

The E3 LangGraph is unchanged. ``graphs.resilient.runner`` turns this package
on with ``harness_scope``. Callers import submodules directly (``context``,
``retry``, ``timeout``, ``unstable``, ``adapters``, ``citations``, ``degrade``,
``verify_output``, ``demo``).
"""
