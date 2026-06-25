"""Provider adapters: stable interfaces isolating all vendor-specific code.

Every adapter implements :class:`~pipelinekit.adapters.base.BaseAdapter` and is
replaceable. Provider libraries (dlt, dbt, Soda) are imported *only* inside
their own adapter packages — never in runtime, cli, config, state, or core.
"""
