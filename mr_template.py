#!/usr/bin/env python3
import os
import sys
import requests
import json
import mr_template_constants
import argparse

env_vars = os.environ.copy()

def get_commit_mrs():

    """

    The function hits the commits api and gets all the merge requests corresponding to it

    :return: commit's merge requests
    :rtype: object

    """
    try:
        endpoint = f"{mr_template_constants.GITLAB_BASE_ENDPOINT}/projects/{env_vars['CI_PROJECT_ID']}/repository/commits/{env_vars['CI_COMMIT_SHORT_SHA']}/merge_requests"
        print(f"Getting the list of all the merge requests corresponding to the given commit, endpoint is: {endpoint}")
        commit_mrs = requests.get(endpoint, headers = {"PRIVATE-TOKEN": env_vars['GITLAB_TOKEN']})
        commit_mrs.raise_for_status()
        commit_mrs = commit_mrs.json()
        return commit_mrs
    except requests.exceptions.HTTPError as err:
        print(err)
        print('An error occurred while getting the merge requests of a commit')

def get_mr_for_target_branch(commit_mrs):

    """

    The function filters the merge request which has target_branch equal to the current branch (i.e., CI_COMMIT_BRANCH)
    :param commit_mrs: all the merge requests of a commit
    :return: merge request corresponding to the target branch 
    :rtype: object

    """

    try:
        if commit_mrs:
            mr_for_target_branch = list(filter(lambda x: x['target_branch'] == env_vars['CI_COMMIT_BRANCH'], commit_mrs))
            print('mr_for_target_branch', mr_for_target_branch)
            mr_for_target_branch = mr_for_target_branch[0]
            return mr_for_target_branch
    except RuntimeError as re:
        print(re)
        print('An error occurred while fetching the merge request corresponding to the target branch')


def create_mr_template_json(mr_for_target_branch, header_text):

    """

    The function converts the mr teamplate into a list, looks for the merge request's header text and stores the information of impacted/non-impacted (based on enabled/disabled checkboxes) components in a json file
    :param: mr_for_target_branch: merge request corresponding to the target branch 
    :param: header_text: text following which the component checkboxes need to be captured

    """

    try:
        mr_template = mr_for_target_branch['description']
        if mr_template:
            mr_template = mr_template.splitlines()
            if header_text in mr_template:
                for i, val in enumerate(mr_template):
                    if val == header_text:
                        mr_template_dict = create_mr_template_dict(mr_for_target_branch['iid'], mr_template, header_text, i+1)
                        print('mr_template_dict', mr_template_dict)
                        if mr_template_dict:
                            with open("mr_template.json", "w") as fp:
                                json.dump(mr_template_dict, fp)
                            break
                        else:
                            print(f"No checkboxes found for the merge request header text: {header_text}")
            else:
                print(f"merge request template does not contain the header text: {header_text}")
        else:
            print('Skipping the creation of merge request template json as the does not have any description')
    except RuntimeError as re:
        print(re)
        print('An error occurred while creating the merge request template json')



def create_mr_template_dict(mr_iid, mr_template, header_text, header_text_index):

    """

    The function creates a dictionary of the merge request's checkboxes along with their enabled/disabled information.

    :return: dictionary of checkboxes along with their enabled/disabled information
    :rtype: dict

    """

    try:

        mr_template_dict = { "mr_iid" : mr_iid, "template_info": {"header_text": header_text, "impacted_components": [], "non_impacted_components": []} }

        for val in range(header_text_index, len(mr_template)):
            mr_template[val] = mr_template[val].strip()
            if mr_template[val].startswith(mr_template_constants.ENABLED_CHECKBOX_MARKDOWN):
                checkbox_text = mr_template[val].split(mr_template_constants.ENABLED_CHECKBOX_MARKDOWN)
                mr_template_dict["template_info"]["impacted_components"].append(checkbox_text[1])
            elif mr_template[val].startswith(mr_template_constants.DISABLED_CHECKBOX_MARKDOWN):
                checkbox_text = mr_template[val].split(mr_template_constants.DISABLED_CHECKBOX_MARKDOWN)
                mr_template_dict["template_info"]["non_impacted_components"].append(checkbox_text[1])
            elif mr_template[val] is None or mr_template[val] == '' or mr_template[val] == ' ':
                continue
            else:
                break
        return mr_template_dict
    except RuntimeError as re:
        print(re)
        print('An error occurred while creating the merge request template dictionary')




def main():

    """

    The functions pefroms the following steps:
     - Gets the content of the merge request template 
     - Looks for the Header Text corresponding to which the checkboxes should be retrieved
     - Grabs the content corresponding to the chekboxes along  with their enabled/disabled information and stores them in a json file

    """

    try:
        commit_mrs = get_commit_mrs()
        if commit_mrs:
            mr_for_target_branch = get_mr_for_target_branch(commit_mrs)
            if mr_for_target_branch:
                mr_template_json = create_mr_template_json(mr_for_target_branch, env_vars['MERGE_REQUEST_HEADER_TEXT'])
                return 0
        else:
            print(f"Skipping the creation of merge request template json as no merge requests found for the commit: {env_vars['CI_COMMIT_SHORT_SHA']}")
            
    except RuntimeError as re:
        print('Oops!! An exception occurred!')
        print(re)

if __name__ == "__main__":
    sys.exit(main())
