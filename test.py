#!/usr/bin/env python3
import os
import re
import sys
import semver
import subprocess
import requests
import re

import constants


def get_recent_tag_without_prefix(prefix):
    """
    The functions get the most recent tag (without the specified prefix) reachable from a commit

    :param prefix: prefix attached to the tag
    :return: Removes the prefix from the most recent tag reachable from a commit and returns it
    :rtype: str
    
    """

    try: 
        recent_tag_with_prefix = get_recent_tag_with_prefix(prefix)
        recent_tag_without_prefix = remove_prefix(prefix, recent_tag_with_prefix)
        return recent_tag_without_prefix

    except subprocess.CalledProcessError:
        # Default to version 0.0.0 if no tags are available
        print('No tags found, hence defaulting to version 0.0.0')
        recent_tag_without_prefix = "0.0.0"
        return recent_tag_without_prefix

def get_recent_tag_with_prefix(prefix):

    """
    The function looks for the most recent tag reachable from a commit & matching the glob pattern

    :param prefix: prefix through which the glob pattern is to be matched
    :return: Returns the most recent tag reachable from a commit & matching the glob pattern
    :rtype: str
    
    """
    
    # Get the most recent tag with the specified prefix, reachable from a commit
    glob = f"{prefix}[0-9]*"
    recent_tag_with_prefix = git("describe", "--tags", "--match", glob).decode().strip()
    print(f'most recent tag reachable from a commit is: {recent_tag_with_prefix}')
    return recent_tag_with_prefix

def git(*args):

    """
    The function takes in git arguments and executes them

    :param args: git command arguments
    :return: Returns the output of git commands
    :rtype: str
    
    """
    
    return subprocess.check_output(["git"] + list(args))

def remove_prefix(prefix, text):

    """
    The function removes the prefix from the provided string

    :param prefix: prefix which needs to be removed from the string
    :param text: string from which the prefix needs to be removed
    :return: Returns the string without the prefix
    :rtype: str
    
    """
    if re.search(prefix, text, re.IGNORECASE):
        return text[len(prefix):]
    return text

def is_tag_bumping_required(recent_tag_without_prefix):

    """
    The function checks if tag bumping is required or not

    :param prefix: The recent tag without the specified prefix
    :return: Returns False if the tag doesn't contain a '-' or doesn't follow semver scheme, otherwise returns True
    :rtype: bool
    
    """

    # skip version bumping if a commit is already tagged
    if is_commit_already_tagged(recent_tag_without_prefix):
        print(f'Skipping version bumping as the most recent commit: {recent_tag_without_prefix} is already tagged')
        return False
    # skip version bumping if a tag does not follow semver scheme
    elif not is_tag_semver(recent_tag_without_prefix):
        print(f'Skipping version bumping as the most recent tag does not not follow the semantic versioning scheme. Read more about semver here: https://semver.org')
        return False
    else:
        return True



def is_commit_already_tagged(recent_tag_without_prefix):
    res = re.search(".*?-g[0-9a-z]{7}$", recent_tag_without_prefix)
    return res

def is_tag_semver(tag):

    """
    The function checks if the tag follows the semver scheme or not

    :param tag: The recent tag which needs to be matched against the regex
    :return: Compares the tag against the regex and returns a match object if the search is successful or None otherwise
    :rtype: object or None
    
    """

    res = re.search("^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$", tag)
    return res

def get_latest_commit_sha():

    """
    The function fetches the sha of the most recent commit

    :return: Returns the commit sha
    :rtype: string
    
    """
    
    print('Getting the sha of the most recent commit...')
    commit_sha = git("rev-parse", "--short", "HEAD").decode().strip()
    return commit_sha
    
def get_bump_version_info(recent_tag_without_prefix, commit_sha):

    """
    The function gets the information required for bumping the tag

    :param recent_tag_without_prefix: The recent tag without the specified prefix
    :param commit_sha: commit sha
    :return: Returns the tag name based on semver bumping
    :rtype: str
    :return: Returns the message that needs to be committed for the tag
    :rtype: str
    
    """

    merge_request_labels, merge_request_title = extract_merge_request_info(commit_sha)
    tag_message = merge_request_title
    tag_name = ''

    if constants.VERSION_MAJOR in merge_request_labels:
        tag_name = semver.bump_major(recent_tag_without_prefix)
    elif constants.VERSION_MINOR in merge_request_labels:
        tag_name = semver.bump_minor(recent_tag_without_prefix)
    else:
        tag_name = semver.bump_patch(recent_tag_without_prefix)
    
    print(f'Tag Bump Version is: {tag_name}')
    return tag_name, tag_message

def extract_merge_request_info(commit_sha):

    """
    The function fetches the merge request information corresponding to a commit

    :param commit_sha: commit sha
    :return merge_request_labels: Returns the labels assigned to a Merge Request
    :rtype: list
    :return: Title of the Merge Request
    :rtype: str
    
    """

    project_id = os.environ["CI_PROJECT_ID"]
    endpoint = f"{constants.BASE_ENDPOINT}/projects/{project_id}/repository/commits/{commit_sha}/merge_requests"
    print(f"Getting the list of all the merge requests corresponding to the given commit, endpoint is: {endpoint}")
    merge_requests_response = requests.get(endpoint, headers = {"PRIVATE-TOKEN": os.environ.get(constants.CI_PRIVATE_TOKEN)})
    merge_request_labels = merge_requests_response.json()[0]['labels']
    print(f'Label(s) available for the most recent merge request: {merge_request_labels}')
    merge_request_title = merge_requests_response.json()[0]['title']
    print(f'Title of the most recent merge request: {merge_request_title}')

    return merge_request_labels, merge_request_title

def tag_commit(tag_name_with_prefix, commit_sha, tag_message):

    """
    The function associates a tag to a commit through its sha and pushes it to the remote repo

    :param tag_name_with_prefix: Name of the annoatated tag (with the specified prefix) that needs to be pushed
    :param commit_sha: commit sha
    :param tag_message: Message for the annotated tag
    :return 
    
    """

    project_id = os.environ["CI_PROJECT_ID"]
    endpoint = f'{constants.BASE_ENDPOINT}/projects/{project_id}/repository/tags?tag_name={tag_name_with_prefix}&ref={commit_sha}&message={tag_message}'
    print(f'Pushing the commit to the remote repository, endpoint is: {endpoint}')
    tags_response = requests.post(endpoint, headers = {"PRIVATE-TOKEN": os.environ.get(constants.CI_PRIVATE_TOKEN)})
    return tags_response.json()

def main():

    """

    The functions pefroms the following steps:
     - Gets the most recent tag reachable from a commit, 
     - Checks if bumping of tag is required
     - Bumps the tag version as per the commit's MR label
     - Pushes an annotated tag to the remote repo

    """

    try:
        # get the most recent tag without the specified prefix, reachable from a commit
        recent_tag_without_prefix = get_recent_tag_without_prefix(constants.PREFIX)

        # check if bumping of tag is required by validating if the last tag is reachable from a commit and is following semver scheme or not
        if recent_tag_without_prefix == '0.0.0':
            is_bumping_required = True
        else:
            is_bumping_required = is_tag_bumping_required(recent_tag_without_prefix)
            
        # perform version bumping if all tag validation checks pass
        if is_bumping_required:
            commit_sha = get_latest_commit_sha()
            print(f'sha of the most recent commit is: {commit_sha}')
            # get the annotated tag's name i.e., the version to be bumped and its corresponding message
            tag_name, tag_message = get_bump_version_info(recent_tag_without_prefix, commit_sha)
            tag_name_with_prefix = f'{constants.PREFIX}{tag_name}'
            # commit the tag to the remote repo
            tag_commit_response = tag_commit(tag_name_with_prefix, commit_sha, tag_message)
            print(f'Tag commit response is: {tag_commit_response}')
            return 0
    except RuntimeError as re:
        print('Oops!! An exception occurred while semver tagging!')
        print(re)

    

if __name__ == "__main__":
    sys.exit(main())
