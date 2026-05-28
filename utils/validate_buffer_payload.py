def validate_create_post_payload(payload: dict) -> tuple[bool, list[str]]:
    errors = []

    params = payload.get("params", {})
    if params.get("name") != "create_post":
        errors.append("params.name must be 'create_post'")

    arguments = params.get("arguments", {})
    if not arguments.get("organizationId"):
        errors.append("arguments.organizationId is required")
    if not arguments.get("channelId"):
        errors.append("arguments.channelId is required")
    if not arguments.get("text"):
        errors.append("arguments.text is required")

    assets = arguments.get("assets", [])
    if not isinstance(assets, list):
        errors.append("arguments.assets must be an array")
    else:
        for i, asset in enumerate(assets):
            if not isinstance(asset, dict):
                errors.append(f"arguments.assets[{i}] must be an object")
            elif not asset.get("url"):
                errors.append(f"arguments.assets[{i}].url is required")

    return len(errors) == 0, errors
