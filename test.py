#!/usr/bin/env python3
import os
import re
import sys
import semver
import subprocess
import requests
import re

import auto_semver_tag_constants


def get_commit_tag():

    """

    The git command used here is 'git describe --tags --match "glob pattern"'
    The function looks for the most recent tag reachable from a commit & matching the glob pattern

    If the tag points to the commit, then only the tag is shown.
    Example: 1.2.3

    Otherwsie, it suffixes the tag name with the number of additional commits on top of the tagged object
    and the abbreviated SHA of the most recent commit
    Example: 1.2.3-7-g1282be01 (Here 7 indicates the number of additional commits and g1282be01 indicates the abbreviated SHA)

    :param prefix: prefix through which the glob pattern is to be matched
    :return: Returns the most recent tag reachable from a commit & matching the glob pattern
    :rtype: str
    
    """
    try:
        # Get the most recent tag with the specified prefix, reachable from a commit
        glob = f"{auto_semver_tag_constants.PREFIX}[0-9]*"
        commit_tag = git("describe", "--tags", "--match", glob).decode().strip()
        print(f'most recent tag reachable from a commit is: {commit_tag}')
        return commit_tag

    except subprocess.CalledProcessError:
        # Default to version 0.0.0 if no tags are available
        print('No tags found, hence defaulting to version 0.0.0')
        commit_tag = "0.0.0"
        return commit_tag

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

def is_tag_bumping_required(commit_tag):

    """
    The function checks if tag bumping is required or not

    :param prefix: The recent tag without the specified prefix
    :return: Returns False if the tag already points to a commit or doesn't follow semver scheme, otherwise returns True
    :rtype: bool
    
    """

    commit_tag_without_prefix = remove_prefix(auto_semver_tag_constants.PREFIX, commit_tag)


    # If commit_tag ends with an abbreviated comit SHA (starting with a g), it implies that there are additional commits and those commits are not tagged yet (example tag name: 1.2.3-7-g1282be01)
    # Whereas if commit_tag doesn't end with an abbreviated commit SHA, it implies that the tag is already pointing to the current HEAD (example tag name: 1.2.3)
    # Hence, version bumping should be skipped
    if not is_tag_pointing_to_latest_commit(commit_tag):
        print(f'Skipping version bumping as the most recent tag: {commit_tag} is already pointing to the latest commit')
        return False
    # skip version bumping if a tag does not follow semver scheme
    elif not is_tag_semver(commit_tag_without_prefix):
        
        print(f'Skipping version bumping as the most recent tag does not not follow the semantic versioning scheme. Read more about semver here: https://semver.org')
        return False
    else:
        return True

def is_tag_pointing_to_latest_commit(commit_tag):

    """
    The function checks if the tag is already pointing to the latest commit or not

    :param commit_tag: The recent tag without the specified prefix
    :return: Compares the tag against the regex and returns a match object if the tag ends with an abbreviated commit starting with '-g' (like 1.2.3) or None otherwise
    :rtype: object or None
    """

    res = re.search(".*?-g[0-9a-z]{7}$", commit_tag)
    return res

def is_tag_semver(tag):

    """
    The function checks if the tag follows the semver scheme or not
    Few examples of valid semantic version:
        0.0.4
        1.2.3
        10.20.30
        1.1.2-prerelease+meta
        1.1.2+meta
    Few examples of invalid semantic version:
        1
        1.2
        1.2.3-0123
        alpha
        +invalid

    More details on the regex and valid/invalid semantic versions can be found here: 'https://regex101.com/r/Ly7O1x/3/'

    :param tag: The recent tag which needs to be matched against the regex
    :return: Compares the tag against the regex and returns a match object if the search is successful or None otherwise
    :rtype: object or None
    
    """
    res = re.search("^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$", tag)
    return res

def get_commit_tag_without_sha():
    try:
        glob = f"{auto_semver_tag_constants.PREFIX}[0-9]*"
        commit_tag_without_sha = git("describe", "--tags", "--match", glob, "--abbrev=0").decode().strip()
        return commit_tag_without_sha
    except subprocess.CalledProcessError:
        raise Exception('Exception occurred while retrieving recent tag reachable from commit (without commit SHA)')

def get_commits_since_last_tag(commit_tag):
    commits_since_last_tag = git("log", "--first-parent", "--pretty=%h", f"{commit_tag}..HEAD").decode().strip()   
    return commits_since_last_tag


def get_latest_commit_sha():

    """
    The function fetches the sha of the most recent commit

    :return: Returns the commit sha
    :rtype: string
    
    """
    
    print('Getting the sha of the most recent commit...')
    commit_sha = git("rev-parse", "--short", "HEAD").decode().strip()
    return commit_sha


def get_bump_version_info(commit_tag_without_sha, commits_since_last_tag):

    """
    The function gets the information required for bumping the tag

    :param commit_tag_without_sha: The recent tag without the specified prefix
    :param commit_sha: commit sha
    :return: Returns the tag name based on semver bumping
    :rtype: str
    :return: Returns the message that needs to be committed for the tag
    :rtype: str
    
    """

    commit_tag_without_prefix = remove_prefix(auto_semver_tag_constants.PREFIX, commit_tag_without_sha)

    list_commits_since_last_tag = commits_since_last_tag.splitlines()
    list_commits_since_last_tag.reverse()

    commit_sha = ''
    tag_name = commit_tag_without_prefix

    for line in list_commits_since_last_tag:
        commit_sha = line
        print("commit_sha", commit_sha)
        merge_request_labels, merge_request_title = extract_merge_request_info(commit_sha)
        tag_message = merge_request_title
        

        if auto_semver_tag_constants.VERSION_MAJOR in merge_request_labels:
            tag_name = semver.bump_major(tag_name)
        elif auto_semver_tag_constants.VERSION_MINOR in merge_request_labels:
            tag_name = semver.bump_minor(tag_name)
        else:
            tag_name = semver.bump_patch(tag_name)
            
    print(f'Bump version info: {commit_sha},{auto_semver_tag_constants.PREFIX}{tag_name}, {tag_message}')
    return commit_sha, f"{auto_semver_tag_constants.PREFIX}{tag_name}", tag_message



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
    endpoint = f"{auto_semver_tag_constants.BASE_ENDPOINT}/projects/{project_id}/repository/commits/{commit_sha}/merge_requests"
    print(f"Getting the list of all the merge requests corresponding to the given commit, endpoint is: {endpoint}")
    merge_requests_response = requests.get(endpoint, headers = {"PRIVATE-TOKEN": os.environ.get(auto_semver_tag_constants.CI_PRIVATE_TOKEN)})
    merge_request_labels = merge_requests_response.json()[0]['labels']
    print(f'Label(s) available for the most recent merge request: {merge_request_labels}')
    merge_request_title = merge_requests_response.json()[0]['title']
    print(f'Title of the most recent merge request: {merge_request_title}')

    return merge_request_labels, merge_request_title

def tag_commit(tag_name, commit_sha, tag_message):

    """
    The function associates a tag to a commit through its sha and pushes it to the remote repo

    :param tag_name: Name of the annoatated tag (with the specified prefix) that needs to be pushed
    :param commit_sha: commit sha
    :param tag_message: Message for the annotated tag
    :return 
    
    """

    project_id = os.environ["CI_PROJECT_ID"]
    endpoint = f'{auto_semver_tag_constants.BASE_ENDPOINT}/projects/{project_id}/repository/tags?tag_name={tag_name}&ref={commit_sha}&message={tag_message}'
    print(f'Pushing the commit to the remote repository, endpoint is: {endpoint}')
    tags_response = requests.post(endpoint, headers = {"PRIVATE-TOKEN": os.environ.get(auto_semver_tag_constants.CI_PRIVATE_TOKEN)})
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
        commit_tag = get_commit_tag()
        # check if bumping of tag is required by validating if the last tag is reachable from a commit and is following semver scheme or not
        if commit_tag == '0.0.0':
            is_bumping_required = True
        else:
            is_bumping_required = is_tag_bumping_required(commit_tag)
            
        # perform version bumping if all tag validation checks pass
        if is_bumping_required:
            
            commit_tag_without_sha = get_commit_tag_without_sha()
            commits_since_last_tag = get_commits_since_last_tag(commit_tag_without_sha)
            print(f"commits_since_last_tag: {commits_since_last_tag}")
            # get the annotated tag's name i.e., the version to be bumped and its corresponding message
            commit_sha, tag_name, tag_message = get_bump_version_info(commit_tag_without_sha, commits_since_last_tag)
            # commit_tag = f'{auto_semver_tag_constants.PREFIX}{tag_name}'
            # commit_sha = get_latest_commit_sha()
            # print(f'sha of the most recent commit is: {commit_sha}')
            # commit the tag to the remote repo
            tag_commit_response = tag_commit(tag_name, commit_sha, tag_message)
            print(f'Tag commit response is: {tag_commit_response}')
            return 0
    except RuntimeError as re:
        print('Oops!! An exception occurred while semver tagging!')
        print(re)

    

if __name__ == "__main__":
    sys.exit(main())
