"""OHLCV source registry (reel task 5). One concrete adapter is chosen at decision B1.

Each registration records: source_id, source_class=EXCHANGE_PUBLIC_DATA, allowed_hosts,
license_class (REDISTRIBUTABLE or REFETCH_ONLY), terms URL and the date the terms were read.
"""
