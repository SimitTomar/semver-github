#!/usr/bin/env python3
import os
import re
import sys
import semver
import subprocess
import requests
import re

import constants

def git(*args):
    return subprocess.check_output(["git"] + list(args))


def get_latest_commit_sha():
    commit_sha = git("rev-parse", "--short", "HEAD").decode().strip()
    return commit_sha


def extract_merge_request_label(_commit_sha):
    
    # TODO: project_id = os.environ["CI_PROJECT_ID"]
    # print('project_id', project_id)
    project_id = 29648219
    # url = 'https://gitlab.com/api/v4/projects/29648219/repository/commits/87fe173/merge_requests'
    url = f'https://gitlab.com/api/v4/projects/{project_id}/repository/commits/{_commit_sha}/merge_requests'
    print('url', url)
    # TODO: replace headers
    merge_requests_response = requests.get(url, headers = {"PRIVATE-TOKEN": "-kU_ac9Atq6txW8h6Xh4"})
    print('merge_requests_response', merge_requests_response.json())
    latest_merge_request = merge_requests_response.json()[0]

    if constants.VERSION_MAJOR in latest_merge_request['labels']:
        return 'major'
    elif constants.VERSION_MINOR in latest_merge_request['labels']:
        return 'minor'
    else:
        return 'patch'


def get_bump_version(_latest):

    commit_sha = get_latest_commit_sha()
    print('commit_sha', commit_sha)

    merge_request_label = extract_merge_request_label(commit_sha)
    print('merge_request_label', merge_request_label)

    bump_version = ''
    if merge_request_label == 'major':
        bump_version = semver.bump_major(_latest)
        print('MAJOR Bump Version', bump_version)

    elif merge_request_label == 'minor':
        bump_version = semver.bump_minor(_latest)
        print('MINOR Bump Version', bump_version)

    else:
        bump_version = semver.bump_patch(_latest)
        print('PATCH Bump Version', bump_version)
    
    return bump_version


def tag_repo(tag):

    print('tag', tag)
    url = os.environ["CI_REPOSITORY_URL"]
    print('url', url)

    push_url = re.sub(r'.+@([^/]+)/', r'git@\1:', url)

    git("remote", "set-url", "--push", "origin", push_url)
    git("tag", tag)
    git("push", "origin", tag)


def main():
    try:
        # Get the most recent tag reachable from a commit
        recent_tag = git("describe", "--tags").decode().strip()
    except subprocess.CalledProcessError:
        # Default to version 1.0.0 if no tags are available
        bumped_version = "1.0.0"
    else:
        # Check for Semver format
        # If yes then go ahead else return 1 with a valid message: Latest tag not following semver format
        # Skip already tagged commits
        if '-' not in recent_tag:
            print('recent_tag', recent_tag)
            return 0
    
        bumped_version = get_bump_version(recent_tag)
        print('bumped_version', bumped_version)

    tag_repo(bumped_version)
    print('bumped_version', bumped_version)


    return 0


if __name__ == "__main__":
    sys.exit(main())
