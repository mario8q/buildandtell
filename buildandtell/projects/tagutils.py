def parse_tags(tagstring):
    if not tagstring:
        return []
    tags = []
    for raw in tagstring.split(","):
        tag = raw.strip()
        if len(tag) >= 2 and tag.startswith('"') and tag.endswith('"'):
            tag = tag[1:-1]
        if tag:
            tags.append(tag)
    return list(dict.fromkeys(tags))