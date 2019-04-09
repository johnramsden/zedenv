# __init__.py

import subprocess

__version__ = '0.3.7'


def vcs_release(version: str):
    """
    If in git repo, get git version
    """
    try:
        git_hash = subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'],
            universal_newlines=True, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        return version

    return version + '+git.' + git_hash


def get_release_version(version: str):
    """
    If on a tagged release, use tagged version, else append git hash
    """
    has_tags = None
    try:
        has_tags = subprocess.check_output(
            ['git', 'tag', '-l', '--points-at', 'HEAD'],
            universal_newlines=True, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        pass

    return version if has_tags and has_tags.startswith("v") else vcs_release(version)
