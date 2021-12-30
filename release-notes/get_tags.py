import subprocess
import traceback

class Tags():

    def fetch_all_tags(self):
        try:
            self.git("fetch", "--all", "--tags").decode().strip()
        except:
            print('Oops !! An unhandled exception occured while fetching all the tags from the remote repo')
            traceback.print_exc()

    def get_tags_for_release_notes(self, previous_tag, current_tag, pattern=None):

        """

        The function gets all the tags between the previous tag and current tag
        :param: previous_tag: Tag against which the last build was deployed 
        :param: current_tag: Tag against which the current build has to be deployed 
        :param: pattern: pattern correspnding to which the all the tags need to be retrieved (None by default) 
        :return: list of all the tags between the previous tag and current tag
        :rtype: list
        """

        try:
            if not previous_tag:
                print('No tags found between previous tag and current tag as the previous tag is empty')
                return
            elif not current_tag:
                print('No tags found between previous tag and current tag as the previous tag is empty')
                return
            elif previous_tag == current_tag:
                print(f"No tags found between previous tag {previous_tag} and current tag {current_tag} as both the tags are same")
                return

            tags_refs = f"refs/tags/{pattern}" if pattern is not None else "refs/tags/"
            tags = self.git("for-each-ref", "--sort", "creatordate", "--format", "%(tag)", tags_refs).decode().strip()
            tags_list = tags.splitlines()
            print('tags_list', tags_list)
            if tags_list:
                if previous_tag not in tags_list:
                    print (f"The previous tag {previous_tag} is not available in the repo tags list")
                    return
                elif current_tag not in tags_list:
                    print (f"The current tag {current_tag} is not available in the repo tags list")
                    return
                else:
                    tags_for_release_notes= tags_list[tags_list.index(previous_tag)+1 : tags_list.index(current_tag)]
                    if tags_for_release_notes:
                        print('tags_for_release_notes', tags_for_release_notes)
                        return tags_for_release_notes
                    else:
                        print(f"No tags available between previous tag {previous_tag} and current tag {current_tag}")
                        return

            else:
                print(f"No tags retreived for the specified repository, pattern is: {pattern}")
        except:
            print('Oops !! An unhandled exception occured while getting the tags for release notes')
            traceback.print_exc()

    def git(self, *args):

        """
        The function takes in git arguments and executes them

        :param args: git command arguments
        :return: Returns the output of git commands
        :rtype: str
        
        """
        
        return subprocess.check_output(["git"] + list(args))



if __name__ == "__main__":
    tags = Tags()
    tags.fetch_all_tags()
    tags.get_tags_for_release_notes('v0.0.1', 'v1.0.0', 'v[0-9]*')
