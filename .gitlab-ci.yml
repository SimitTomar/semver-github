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


def get_bump_version(_latest):

    commit_sha = get_latest_commit_sha()
    print(f'sha of the most recent commit is: {commit_sha}')

    merge_request_label = extract_merge_request_label(commit_sha)
    print(f'Merge request label for the most recent merge request is: {merge_request_label}')

    bump_version = ''
    if merge_request_label == 'major':
        bump_version = semver.bump_major(_latest)

    elif merge_request_label == 'minor':
        bump_version = semver.bump_minor(_latest)

    else:
        bump_version = semver.bump_patch(_latest)
    
    print(f'Bump Version is: {bump_version}')
    return bump_version, commit_sha


def get_latest_commit_sha():
    print('Getting the sha of the most recent commit...')
    commit_sha = git("rev-parse", "--short", "HEAD").decode().strip()
    return commit_sha


def extract_merge_request_label(commit_sha):

    project_id = os.environ["CI_PROJECT_ID"]
    endpoint = f"{constants.BASE_ENDPOINT}/projects/{project_id}/repository/commits/{commit_sha}/merge_requests"
    print(f"Getting the list of all the merge requests corresponding to the given commit, endpoint is: {endpoint}")
    merge_requests_response = requests.get(endpoint, headers = {"PRIVATE-TOKEN": os.environ.get(constants.CI_PRIVATE_TOKEN)})
    print('Getting the most recent merge request for the given commit...')
    merge_request_labels = merge_requests_response.json()[0]['labels']
    print(f'Labels available for the most recent merge request: {merge_request_labels}')

    if constants.VERSION_MAJOR in merge_request_labels:
        return 'major'
    elif constants.VERSION_MINOR in merge_request_labels:
        return 'minor'
    else:
        return 'patch'


def tag_repo(tag, commit_sha):

    project_id = os.environ["CI_PROJECT_ID"]
    endpoint = f'{constants.BASE_ENDPOINT}/projects/{project_id}/repository/tags?tag_name={tag}&ref={commit_sha}'
    print(f'Pushing the commit to the remote repository, endpoint is: {endpoint}')
    tags_response = requests.post(endpoint, headers = {"PRIVATE-TOKEN": os.environ.get(constants.CI_PRIVATE_TOKEN)})
    print('Tags response is:', tags_response.json())


def main():
    try:
        # Get the most recent tag reachable from a commit
        recent_tag = git("describe", "--tags").decode().strip()
        print(f'most recent tag reachable from a commit is: {recent_tag}')
    except subprocess.CalledProcessError:
        # Default to version 1.0.0 if no tags are available
        print('No tags found, hence defaulting to version 1.0.0')
        bumped_version = "1.0.0"
    else:
        # TODO:
        # Check for Semver format
        # If yes then go ahead else return 1 with a valid message: Latest tag not following semver format
        # Skip already tagged or non conformant semantic versioning scheme commits
        if '-' not in recent_tag:
            print(f'Skipping version bumping as the most recent commit: {recent_tag} is either already tagged or not conforming to the semantic versioning schem of MAJOR.MINOR.PATCH')
            return 0
    
        bumped_version, commit_sha = get_bump_version(recent_tag)

    tag_repo(bumped_version, commit_sha)
    with open('buid.env', 'w') as f:
        f.write(bumped_version)

    return 0


if __name__ == "__main__":
    sys.exit(main())
