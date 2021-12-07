#!/usr/bin/env python3
import json
import traceback
from mr import Mr
from mr_template import MrTemplate
from mr_jira_ids import MrJiraIds


class MrInfo(Mr):

    def __init__(self):
        super().__init__()

    def get_mr_info(self):

        """

        The functions peforms the following steps:
        - Gets the merge request corresponding to a commit
        - Gets the content of the merge request template
        - Extracts the Jira Ids from commit messages of the respective merge request
        - Cosolidates the template and jira id info and saves them in a json file

        """

        try:
            
            commit_mrs = self.get_commit_mrs()
            if commit_mrs:
                mr_for_target_branch = self.get_mr_for_target_branch(commit_mrs)
                if mr_for_target_branch:
                    mr_template = MrTemplate()
                    mr_template_dict = mr_template.get_mr_template_dict(mr_for_target_branch, self.gitlab_env_vars['MERGE_REQUEST_HEADER_TEXT'])
                    if mr_template_dict:
                        mr_jira_ids = MrJiraIds(self.gitlab_env_vars)
                        mr_jira_ids_list = mr_jira_ids.get_jira_ids_list(mr_for_target_branch)
                        if mr_jira_ids_list:
                            mr_info_dict = {'mr_iid': mr_for_target_branch['iid'], 'template': mr_template_dict, 'jira_ids': mr_jira_ids_list}
                            mr_info_json = json.dumps(mr_info_dict, indent=2)
                            print('mr_info_json: ', mr_info_json)
                            mr_info_json_file = open('mr_info.json', 'w')
                            mr_info_json_file.write(mr_info_json)
                            mr_info_json_file.close()
                            return 0
                        else:
                            print('Getting merge request info skipped as no merge request jira ids found for the corresponding commit messages')
                    else:
                        print('Getting merge request info skipped as either the mr template could not be retrieved or there were no impacted components for the merge request')
                else:
                    print(f"Getting merge request info skipped as no merge request could be retrieved against the corresponding target branch {self.gitlab_env_vars['CI_COMMIT_BRANCH']}")
            else:
                print(f"Getting merge request info skipped as no merge requests could be retrieved for the commit: {self.gitlab_env_vars['CI_COMMIT_SHORT_SHA']}")
        except KeyError:
            print("Oops !! A key error occurred while getting the mr info")
            traceback.print_exc()
        except:
            print("Oops !! An unhandled exception occured while getting the mr info")
            traceback.print_exc()
            

if __name__ == "__main__":
    mr_info = MrInfo()
    mr_info.get_mr_info()
