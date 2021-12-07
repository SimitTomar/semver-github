#!/usr/bin/env python3
import os
import requests
import traceback
import release_notes_constants


class Mr():

    gitlab_env_vars = os.environ.copy()
    # gitlab_env_vars = {'CI_PROJECT_ID': '31630126', 'CI_COMMIT_SHORT_SHA': '69ac0940', 'GITLAB_TOKEN': 'Y_oAQTrTNyTh9Bf4KuYi', 'MR_TEMPLATE_JSON_ENABLED': 'true', 'CI_COMMIT_BRANCH': 'main', 'MERGE_REQUEST_HEADER_TEXT': 'Components impacted by this MR:'}
    
    def get_commit_mrs(self):

        """

        The function gets all the merge requests corresponding to a commit through gitlab's commits api

        :return: commit's merge requests
        :rtype: list

        """

        try:
            endpoint = f"{release_notes_constants.GITLAB_BASE_ENDPOINT}/projects/{self.gitlab_env_vars['CI_PROJECT_ID']}/repository/commits/{self.gitlab_env_vars['CI_COMMIT_SHORT_SHA']}/merge_requests"
            print(f"Getting the list of all the merge requests corresponding to the given commit, endpoint is: {endpoint}")
            commit_mrs = requests.get(endpoint, headers = {"PRIVATE-TOKEN": self.gitlab_env_vars['GITLAB_TOKEN']})
            commit_mrs.raise_for_status()
            commit_mrs = commit_mrs.json()
            return commit_mrs
        except requests.exceptions.HTTPError:
            print('Oops !! An HTTP error occurred while getting the merge requests of a commit')
            traceback.print_exc()
        except KeyError:
            print("Oops !! A key error occurred while getting the merge requests of a commit")
            traceback.print_exc()
        except:
            print("Oops !! An unhandled error occurred while getting the merge requests of a commit")
            traceback.print_exc()

        
    def get_mr_for_target_branch(self, commit_mrs):

        """

        The function filters the merge request which has target_branch equal to the current branch (i.e., CI_COMMIT_BRANCH)
        :param commit_mrs: all the merge requests of a commit
        :return: merge request corresponding to the target branch 
        :rtype: dict

        """

        try:
            if commit_mrs:
                mr_for_target_branch = list(filter(lambda x: x['target_branch'] == self.gitlab_env_vars['CI_COMMIT_BRANCH'], commit_mrs))
                mr_for_target_branch = mr_for_target_branch[0]
                return mr_for_target_branch
        except IndexError:
            print('Oops !! An index error occurred while fetching the merge request corresponding to the target branch')
            traceback.print_exc()
        except KeyError:
            print("Oops !! A key error occurred while fetching the merge request corresponding to the target branch")
            traceback.print_exc()
        except:
            print("Oops !! An unhandled error occurred while fetching the merge request corresponding to the target branch")
            traceback.print_exc()
