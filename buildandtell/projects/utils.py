import re

def is_github_repo(url):
    pattern = r"^https?://github\.com/[^/]+/[^/]+/?$"
    return bool(re.match(pattern, url))