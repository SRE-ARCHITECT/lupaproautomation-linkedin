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
                continue
            image = asset.get("image")
            video = asset.get("video")
            if not image and not video:
                errors.append(f"arguments.assets[{i}] must have 'image' or 'video' property with an object containing 'url'")
            if image and (not isinstance(image, dict) or not image.get("url")):
                errors.append(f"arguments.assets[{i}].image must be an object with a 'url' property")
            if video and (not isinstance(video, dict) or not video.get("url")):
                errors.append(f"arguments.assets[{i}].video must be an object with a 'url' property")

    return len(errors) == 0, errors
