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

    The function returns the most recent tag starting with the specified prefix & reachable from a commit

    If no tag is found matching this condition, then a default tag 0.0.0 is returned
    The git command used here is 'git describe --tags --match "glob pattern"'

    If the tag points to the commit, then only the tag is shown.
    Example: 1.2.3

    Otherwsise, it suffixes the tag name with the number of additional commits on top of the tagged object
    and the abbreviated SHA of the most recent commit
    Example: 1.2.3-7-g1282be01 (Here 7 indicates the number of additional commits and g1282be01 indicates the abbreviated SHA)

    :return: Returns the most recent tag reachable from a commit & matching the glob pattern, otherwise 0.0.0
    :rtype: str
    
    """
    try:
        # Get the most recent tag with the specified prefix, reachable from a commit
        glob = f"{auto_semver_tag_constants.PREFIX}[0-9]*"
        commit_tag = git("describe", "--tags", "--match", glob).decode().strip()
        print(f'most recent tag reachable from a commit is: {commit_tag}')
        return commit_tag

    except subprocess.CalledProcessError:
        # Default to version 0.0.0 if no tags are found
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

def is_tag_bumping_required(commit_tag):

    """
    The function checks if tag bumping is required or not

    :param commit_tag: The most recent tag reachable from a commit
    :return: Returns False if the tag already points to a commit or doesn't follow semver scheme, otherwise returns True
    :rtype: bool
    
    """
    
    commit_tag_without_prefix = remove_prefix(auto_semver_tag_constants.PREFIX, commit_tag)

    # If commit_tag ends with an abbreviated comit SHA (starting with a g), it implies that there are additional commits and those commits are not tagged yet (example tag name: 1.2.3-7-g1282be01)
    # Whereas if commit_tag doesn't end with an abbreviated commit SHA, it implies that the tag is already pointing to the current HEAD (example tag name: 1.2.3)
    # Hence, version bumping should be skipped
    if not is_tag_ending_with_abbreviated_commit_sha(commit_tag):
        print(f'Skipping version bumping as the most recent tag: {commit_tag} is already pointing to the latest commit')
        return False
    # skip version bumping if a tag does not follow semver scheme
    elif not is_tag_semver(commit_tag_without_prefix):
        raise Exception(f'The most recent tag does not not follow the semantic versioning scheme. Read more about semver here: https://semver.org')
    else:
        return True

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

def is_tag_ending_with_abbreviated_commit_sha(commit_tag):

    """
    The function checks if the tag is already pointing to the latest commit or not

    :param commit_tag: The tag which needs to be matched against the abbreviated commit SHA regex
    :return: Compares the tag against the regex and returns a match object if the tag ends with an abbreviated commit starting with '-g' (like 1.2.3) or None otherwise
    :rtype: object or None
    """

    res = re.search(".*?-g[0-9a-z]*$", commit_tag)
    return res

def is_tag_semver(commit_tag):

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

    :param commit_tag: The recent tag which needs to be matched against the semver regex
    :return: Compares the tag against the regex and returns a match object if the search is successful or None otherwise
    :rtype: object or None
    
    """
    res = re.search("^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$", commit_tag)
    return res

def get_commit_tag_without_sha(commit_tag):

    """

    The function retrieves the abbreviated commit SHA releated to the most recent commit tag

    :return: Returns the most recent commit tag reachable from a commit without its associated abbreviated commit SHA
    :rtype: str
    
    """
    try:
        glob = f"{auto_semver_tag_constants.PREFIX}[0-9]*"
        commit_tag_without_sha = git("describe", "--tags", "--match", glob, "--abbrev=0").decode().strip()
        print(f'commit_tag_without_sha: {commit_tag_without_sha}')
        return commit_tag_without_sha
    except subprocess.CalledProcessError:
        raise Exception('Exception occurred while retrieving sha of the most recent commit tag')

def get_commits_since_last_tag(commit_tag_without_sha):

    """

    The function fetches all the commits since the last commit tag

    :param commit_tag_without_sha: Most recent commit tag reachable from a commit without its associated abbreviated commit SHA
    :return: Returns all the commits since the last commit tag
    :rtype: str
    
    """
    commits_since_last_tag = git("log", "--first-parent", "--pretty=%h", f"{commit_tag_without_sha}..HEAD").decode().strip()
    print(f"commits_since_last_tag: {commits_since_last_tag}")
    return commits_since_last_tag

def get_bump_tag_info(commit_tag_without_sha, commits_since_last_tag):

    """
    
    The function iterates through all the commits available after the most recent commit tag and works out the tag version to be bumped and its corresponding message


    :param commit_tag_without_sha: Most recent commit tag reachable from a commit without its associated abbreviated commit SHA
    :param commits_since_last_tag: All the commits since the last commit tag
    :return: Return the commit SHA related to the most recent commit tag
    :rtype: str
    :return: Returns the tag name based on semver bumping
    :rtype: str
    :return: Returns the message that needs to be committed for the tag
    :rtype: str
    
    """

    if not commits_since_last_tag:
        commit_sha = git("rev-parse", "--short", "HEAD").decode().strip()
        bump_tag, tag_message = get_bump_tag_version_and_message(commit_sha, commit_tag_without_sha)

    else:
        list_commits_since_last_tag = []
        commit_tag_without_prefix = remove_prefix(auto_semver_tag_constants.PREFIX, commit_tag_without_sha)
        list_commits_since_last_tag = commits_since_last_tag.splitlines()
        list_commits_since_last_tag.reverse()

        for line in list_commits_since_last_tag:
            commit_sha = line
            bump_tag, tag_message = get_bump_tag_version_and_message(commit_sha, commit_tag_without_prefix)

    print(f"commit_sha: {commit_sha}")
    print(f"bump tag: {auto_semver_tag_constants.PREFIX}{bump_tag}")
    print (f"tag message: {tag_message}")
    return commit_sha, f"{auto_semver_tag_constants.PREFIX}{bump_tag}", tag_message

def get_bump_tag_version_and_message(commit_sha, bump_tag):
    merge_request_labels, merge_request_title = extract_merge_request_info(commit_sha)
    tag_message = merge_request_title
    
    if auto_semver_tag_constants.VERSION_MAJOR in merge_request_labels:
        bump_tag = semver.bump_major(bump_tag)
    elif auto_semver_tag_constants.VERSION_MINOR in merge_request_labels:
        bump_tag = semver.bump_minor(bump_tag)
    else:
        bump_tag = semver.bump_patch(bump_tag)
    return bump_tag, tag_message


def extract_merge_request_info(commit_sha):

    """
    The function fetches the merge request information corresponding to a commit

    :param commit_sha: commit SHA related to the most recent commit tag
    :return merge_request_labels: Returns the labels assigned to a Merge Request
    :rtype: list
    :return: Title of the Merge Request
    :rtype: str
    
    """

    project_id = os.environ["CI_PROJECT_ID"]
    endpoint = f"{auto_semver_tag_constants.GITLAB_BASE_ENDPOINT}/projects/{project_id}/repository/commits/{commit_sha}/merge_requests"
    print(f"Getting the list of all the merge requests corresponding to the given commit, endpoint is: {endpoint}")
    merge_requests_response = requests.get(endpoint, headers = {"PRIVATE-TOKEN": os.environ.get(auto_semver_tag_constants.CI_PRIVATE_TOKEN)})
    merge_request_labels = merge_requests_response.json()[0]['labels']
    print(f'Label(s) available for the most recent merge request: {merge_request_labels}')
    merge_request_title = merge_requests_response.json()[0]['title']
    print(f'Title of the most recent merge request: {merge_request_title}')

    return merge_request_labels, merge_request_title

def tag_commit(bump_tag, commit_sha, tag_message):

    """
    The function associates a tag to a commit through its sha and pushes it to the remote repo

    :param bump_tag: Name of the annoatated tag (with the specified prefix) that needs to be pushed
    :param commit_sha: commit sha
    :param tag_message: Message for the annotated tag
    :return 
    
    """

    project_id = os.environ["CI_PROJECT_ID"]
    endpoint = f'{auto_semver_tag_constants.GITLAB_BASE_ENDPOINT}/projects/{project_id}/repository/tags?tag_name={bump_tag}&ref={commit_sha}&message={tag_message}'
    print(f'Pushing the commit to the remote repository, endpoint is: {endpoint}')
    tags_response = requests.post(endpoint, headers = {"PRIVATE-TOKEN": os.environ.get(auto_semver_tag_constants.CI_PRIVATE_TOKEN)})
    return tags_response.json()

def main():

    """

    The functions pefroms the following steps:
     - Gets the most recent tag reachable from a commit
     - Checks if bumping of tag is required
     - Gets the abbreviated commit SHA related to the most recent tag reachable from a commit
     - Gets all the commits since the last tag
     - Iterates through all the commits and works out the tag version to be bumped and its corresponding message
     - Pushes an annotated tag to the remote repo with the retrieved bump version and tag message

    """

    try:

        # get the most recent tag reachable from a commit
        commit_tag = get_commit_tag()
        # assign 0.0.0 version to no commit_tag if no tag is found
        if commit_tag == '0.0.0':
            is_bumping_required = True
        else:
            # check if bumping of tag is required by validating if the last tag is reachable from a commit and is following semver scheme or not
            is_bumping_required = is_tag_bumping_required(commit_tag)
            
        # perform version bumping if all tag validation checks pass
        if is_bumping_required:
            if commit_tag == '0.0.0':
                commit_tag_without_sha = commit_tag
                commits_since_last_tag = None
            else:
                # get the abbreviated commit SHA related to the most recent tag reachable from a commit
                commit_tag_without_sha = get_commit_tag_without_sha(commit_tag)
                # get all the commits since last tag
                commits_since_last_tag = get_commits_since_last_tag(commit_tag_without_sha)
            # iterate through all the commits and work out the tag version to be bumped and its corresponding message
            commit_sha, bump_tag, tag_message = get_bump_tag_info(commit_tag_without_sha, commits_since_last_tag)
            # commit the tag to the remote repo
            tag_commit_response = tag_commit(bump_tag, commit_sha, tag_message)
            print(f'Tag commit response is: {tag_commit_response}')
            return 0
    except RuntimeError as re:
        print('Oops!! An exception occurred while semver tagging!')
        print(re)

if __name__ == "__main__":
    sys.exit(main())
