import requests
from django.utils.dateparse import parse_datetime
from projects.models import BuildUpdate

def fetch_github_commits(owner, repo):
    url = f'https://api.github.com/repos/{owner}/{repo}/commits?commiter={owner}'
    headers = {
        'accept': 'application/vnd.github+json',
    }
    response = requests.request('GET', url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Error al conectar con GitHub: {response.status_code} - {response.text}")
    commits_list = response.json()
    return commits_list

def create_build_updates_from(commits_list, owner, repo, project):
    for commit_meta in commits_list:
        sha = commit_meta['sha']
        title = commit_meta['commit']['message']
        bu_type = BuildUpdate.UpdateType.GITHUB_COMMIT
        body = f'https://github.com/{owner}/{repo}/commit/{sha}'
        created = parse_datetime(commit_meta['commit']['committer']['date'])
        BuildUpdate.objects.create(project=project, title=title, type=bu_type, body=body, created=created)
    return True