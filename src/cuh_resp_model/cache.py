"""Cache for background tasks."""

import diskcache
from dash import DiskcacheManager

cache = diskcache.Cache('./cache')
bg_manager = DiskcacheManager(cache)
