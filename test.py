#!/usr/bin/env python3
import os
import re
import sys
import semver
import subprocess
import requests
import re

import constants


def get_recent_tag():
    # Get the most recent tag reachable from a commit
    recent_tag = git("describe", "--tags").decode().strip()
    print(f'most recent tag reachable from a commit is: {recent_tag}')
    return recent_tag

def git(*args):
    return subprocess.check_output(["git"] + list(args))

def remove_prefix(prefix, text):
    if re.search(prefix, text, re.IGNORECASE):
        return text[len(prefix):]
    return text

def is_tag_semver(tag):
    res = re.search("^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$", tag)
    return res


def get_latest_commit_sha():
    print('Getting the sha of the most recent commit...')
    commit_sha = git("rev-parse", "--short", "HEAD").decode().strip()
    return commit_sha
    

def get_bump_version(_recent_tag_without_prefix, _commit_sha):

    merge_request_labels = extract_merge_request_labels(_commit_sha)
    bump_version = ''
    if constants.VERSION_MAJOR in merge_request_labels:
        bump_version = semver.bump_major(_recent_tag_without_prefix)
    elif constants.VERSION_MINOR in merge_request_labels:
        bump_version = semver.bump_minor(_recent_tag_without_prefix)
    else:
        bump_version = semver.bump_patch(_recent_tag_without_prefix)
    
    print(f'Bump Version is: {bump_version}')
    return bump_version


def extract_merge_request_labels(commit_sha):

    project_id = os.environ["CI_PROJECT_ID"]
    endpoint = f"{constants.BASE_ENDPOINT}/projects/{project_id}/repository/commits/{commit_sha}/merge_requests"
    print(f"Getting the list of all the merge requests corresponding to the given commit, endpoint is: {endpoint}")
    merge_requests_response = requests.get(endpoint, headers = {"PRIVATE-TOKEN": os.environ.get(constants.CI_PRIVATE_TOKEN)})
    print('Getting the most recent merge request for the given commit...')
    merge_request_labels = merge_requests_response.json()[0]['labels']
    print(f'Label(s) available for the most recent merge request: {merge_request_labels}')
    return merge_request_labels



def tag_repo(tag, commit_sha):

    project_id = os.environ["CI_PROJECT_ID"]
    endpoint = f'{constants.BASE_ENDPOINT}/projects/{project_id}/repository/tags?tag_name={tag}&ref={commit_sha}'
    print(f'Pushing the commit to the remote repository, endpoint is: {endpoint}')
    tags_response = requests.post(endpoint, headers = {"PRIVATE-TOKEN": os.environ.get(constants.CI_PRIVATE_TOKEN)})
    print('Tags response is:', tags_response.json())


def main():

    try: 
        recent_tag = get_recent_tag()
        recent_tag_without_prefix = remove_prefix(constants.PREFIX, recent_tag)

    # this block will be executed in case an exception occurs
    except subprocess.CalledProcessError:
        # Default to version 0.0.0 if no tags are available
        print('No tags found, hence defaulting to version 0.0.0')
        recent_tag_without_prefix = "0.0.0"
    
    # this block will be executed if there is no exception in the try block
    else:
        # TODO: Check if a commit is already tagged
        # Skip if a commit is already tagged
        if '-' not in recent_tag_without_prefix :
            print(f'Skipping version bumping as the most recent commit: {recent_tag_without_prefix} is already tagged')
            return 0
        elif not is_tag_semver(recent_tag_without_prefix):
            print(f'most recent tag is not following the semantic versioning scheme')
            return 0

    commit_sha = get_latest_commit_sha()
    print(f'sha of the most recent commit is: {commit_sha}')
    bumped_version = get_bump_version(recent_tag_without_prefix, commit_sha)
    bumped_version_with_prefix = f'{constants.PREFIX}{bumped_version}'
    tag_repo(bumped_version_with_prefix, commit_sha)

    return 0

if __name__ == "__main__":
    sys.exit(main())

