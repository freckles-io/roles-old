import fnmatch
import os

from ansible.module_utils.basic import *
from ansible.module_utils.basic import AnsibleModule

FRECKLES_PACKAGE_METADATA_FILENAME = ".package.freckles"
NO_INSTALL_MARKER_FILENAME = ".no_install.freckles"
NO_STOW_MARKER_FILENAME = ".no_stow.freckles"

FRECKLES_FOLDER_MARKER_FILENAME = ".freckles"

def create_dotfiles_dict(dotfile_repos, profiles=None):
        """Walks through all the provided dotfiles, and creates a dictionary with values according to what it finds, per folder.

        Args:
           dotfile_repos (list): a list of dotfile dictionaries (see: XXX)
           profiles (list): a list of strings indicating with profiles (sub-folders) to process
        """

        apps = []

        for repo in dotfile_repos:
            dest = repo.get("dest", False)
            repo = repo.get("repo", False)

            if not dest:
                raise Exception("Dotfile repo description does not contain 'dest' key: {}".format(repo))
            if not repo:
                raise Exception("Dotfile repo description does not contain 'repo' key: {}".format(repo))

            if not profiles:
                paths = []
                for root, dirnames, filenames in os.walk(os.path.expanduser(dest)):
                    for filename in fnmatch.filter(filenames, FRECKLES_FOLDER_MARKER_FILENAME):
                        paths.append(root)
            else:
                paths = profiles

            if not paths:
                paths = [""]

            for dotfile_path in paths:

                temp_full_path = os.path.expanduser(os.path.join(dest, dotfile_path))

                if not os.path.isdir(temp_full_path):
                    # ignoring, not a directory
                    continue

                if not dotfile_path:
                    freckles_profile = None
                else:
                    freckles_profile = os.path.basename(dotfile_path)

                for item in os.listdir(temp_full_path):
                    if not item.startswith(".") and os.path.isdir(os.path.join(temp_full_path, item)):
                        # defaults
                        dotfile_dir = os.path.join(temp_full_path, item)
                        app = {}
                        app['folder_name'] = item
                        if freckles_profile:
                            app['freckles_profile'] = freckles_profile
                        app['dotfile_dotfile_dir'] = dotfile_dir
                        app['dotfile_parent_path'] = temp_full_path
                        app['dotfile_dest'] = dest
                        if repo:
                            app['dotfile_repo'] = repo
                        if dotfile_path:
                            app['dotfile_relative_path'] = dotfile_path

                        freckles_metadata_file = os.path.join(dotfile_dir, FRECKLES_PACKAGE_METADATA_FILENAME)
                        if os.path.exists(freckles_metadata_file):
                            # have to assume no pyyaml is available
                            with open(freckles_metadata_file, "r") as f:
                                data = f.read()
                            app['freckles_metadata_content'] = data
                            # stream = open(freckles_metadata_file, 'r')
                            # temp = yaml.safe_load(stream)
                            # app.update(temp)

                        no_install_file = os.path.join(dotfile_dir, NO_INSTALL_MARKER_FILENAME)
                        if os.path.exists(no_install_file):
                            app['no_install'] = True

                        no_stow_file = os.path.join(dotfile_dir, NO_STOW_MARKER_FILENAME)
                        if os.path.exists(no_stow_file):
                            app['no_stow'] = True

                        # if "name" not in app.keys():
                            # if app.get("pkg_mgr", None) == "git" and "repo" in app.keys():
                                # app["name"] = app["repo"]
                            # else:
                                # app["name"] = item
                        package_dict = {"packages": {item: app}}
                        apps.append(package_dict)

        # format = {"child_marker": "packages",
        #       "default_leaf": "vars",
        #       "default_leaf_key": "name",
        #       "key_move_map": {'*': "vars"}}
        # chain = [frkl.FrklProcessor(format)]

        # frkl_obj = frkl.Frkl(apps, chain)
        # temp = frkl_obj.process()

        return apps


def additional_packages_dict(dotfile_repos, profiles=None):

        pkgs = []
        for dr in dotfile_repos:
            dest = dr["dest"]
            if not profiles:
                for root, dirnames, filenames in os.walk(os.path.expanduser(dest)):
                    for filename in fnmatch.filter(filenames, FRECKLES_FOLDER_MARKER_FILENAME):
                        profiles.append(os.path.relpath(root, os.path.expanduser(dest)))

            if not profiles:
                profiles = [""]

            for p in profiles:
                packages_metadata = os.path.expanduser(os.path.join(dest, p, FRECKLES_FOLDER_MARKER_FILENAME))
                if os.path.exists(packages_metadata):
                    app = {"vars": {"freckles_profile": p}}
                    with open(packages_metadata, "r") as f:
                        data = f.read()
                    app["freckles_metadata_content"] = data
                    pkgs.append(app)
                    # stream = open(packages_metadata, 'r')
                    # temp = yaml.safe_load(stream)
                    # pkgs.append({"vars": {"freckles_profile": p}, "packages": temp})

        # format = {"child_marker": "packages",
                  # "default_leaf": "vars",
                  # "default_leaf_key": "name",
                  # "key_move_map": {'*': "vars"}}
        # chain = [frkl.EnsureUrlProcessor(), frkl.EnsurePythonObjectProcessor(), frkl.FrklProcessor(format)]

        # frkl_obj = frkl.Frkl(pkgs, chain)

        # packages = frkl_obj.process()

        return pkgs


def main():
    module = AnsibleModule(
        argument_spec = dict(
            dotfiles_repos = dict(required=True, type='list'),
            profiles = dict(default=[], required=False, type='list')

        ),
        supports_check_mode=False
    )

    p = module.params

    profiles = p.get('profiles', None)

    dotfile_facts = {}

    dotfile_packages = create_dotfiles_dict(p['dotfiles_repos'], profiles)
    dotfile_facts['freckles_dotfile_packages'] = dotfile_packages

    additional_packages = additional_packages_dict(p['dotfiles_repos'], profiles)
    dotfile_facts['freckles_additional_packages'] = additional_packages

    # executable_exists = {}
    # for exe in p.get('executables_to_check', []):
        # missing = missing_from_path(exe)
        # executable_exists[exe] = not missing
    # dotfile_facts['executable_exists'] = executable_exists

    module.exit_json(changed=False, ansible_facts=dict(dotfile_facts))

if __name__ == '__main__':
    main()
