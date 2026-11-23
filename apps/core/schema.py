def public_demo_routes(endpoints):
    """Keep compatibility aliases reachable without duplicating operations in Swagger."""
    prefixes = ("/accounts/", "/transactions/", "/open-banking/accounts/v1/",
                "/open-banking/consents/v1/")
    return [item for item in endpoints if not item[0].startswith(prefixes)]
