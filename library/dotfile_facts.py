import fnmatch
import os

from ansible.module_utils.basic import *
from ansible.module_utils.basic import AnsibleModule

FRECKLES_PACKAGE_METADATA_FILENAME = ".package.freckles"
NO_INSTALL_MARKER_FILENAME = ".no_install.freckles"
NO_STOW_MARKER_FILENAME = ".no_stow.freckles"

FRECKLES_FOLDER_MARKER_FILENAME = ".freckles"

METADATA_CONTENT_KEY = "freckles_metadata_content"

DEFAULT_PROFILE_NAME = "default_profile"

def find_freckles_folders(freckles_repos, profiles=None):
    """Walks through all the provided dotfiles, and creates a dictionary with values according to what it finds, per folder.

    Args:
      freckles_repos (list): a list of dotfile dictionaries (see: XXX)
      profiles (list): a list of strings indicating with profiles (sub-folders) to process
    """

    freckles_paths = {}
    for r in freckles_repos:

        dest = r.get("dest", False)
        repo = r.get("repo", False)

        if not dest:
            raise Exception("Dotfile repo description does not contain 'dest' key: {}".format(repo))
        if not repo:
            raise Exception("Dotfile repo description does not contain 'repo' key: {}".format(repo))

        temp_paths = {}
        # find all freckles folders
        for root, dirnames, filenames in os.walk(os.path.expanduser(dest)):

            # check whether the folder has got a .freckles marker file
            for filename in fnmatch.filter(filenames, FRECKLES_FOLDER_MARKER_FILENAME):
                if root:
                    profile_name = os.path.basename(root)
                else:
                    profile_name = DEFAULT_PROFILE_NAME

                if profiles and (profile_name == DEFAULT_PROFILE_NAME or profile_name not in profiles):
                    continue

                local_path = os.path.join(os.path.expanduser(dest), root)
                temp_paths[local_path] = {}
                temp_paths[local_path]["profile_name"] = profile_name
                temp_paths[local_path]["remote_repo"] = repo
                temp_paths[local_path]["repo_local_dest"] = dest
                temp_paths[local_path]["relative_path"] = root
                metadata_file = os.path.join(local_path, FRECKLES_FOLDER_MARKER_FILENAME)

                if os.path.exists(metadata_file):
                    with open(metadata_file, "r") as f:
                        data = f.read()
                        if data:
                            temp_paths[local_path][METADATA_CONTENT_KEY] = data

        if not temp_paths:
            profile_name = DEFAULT_PROFILE_NAME
            local_path = os.path.expanduser(dest)
            freckles_paths[local_path] = {}
            freckles_paths[local_path]["profile_name"] = profile_name
            freckles_paths[local_path]["remote_repo"] = repo
            freckles_paths[local_path]["repo_local_dest"] = dest
            freckles_paths[local_path]["relative_path"] = root
            metadata_file = os.path.join(local_path, FRECKLES_FOLDER_MARKER_FILENAME)

            if os.path.exists(metadata_file):
                with open(metadata_file, "r") as f:
                    data = f.read()
                if data:
                    freckles_paths[local_path][METADATA_CONTENT_KEY] = data
        else:
            freckles_paths.update(temp_paths)

    return freckles_paths


def augment_with_dotfile_packages(freckles_folders):
    """Walks through provided freckles folders, assumes every sub-folder is a folder representing an app.

    If such a sub-folder contains a file called .package.freckles, tihs will be read and the (yaml) data in it will be super-imposed on top of the freckles_folder metadata.
    """

    for folder, folder_details in freckles_folders.items():

        profile_name = folder_details['profile_name']
        remote_repo = folder_details['remote_repo']
        local_dest = folder_details['repo_local_dest']
        relative_path = folder_details['relative_path']

        app_folders = []
        for subfolder in os.listdir(folder):

            dotfiles_dir = os.path.join(folder, subfolder)
            if subfolder.startswith(".") or not os.path.isdir(dotfiles_dir):
                continue

            app = {}
            app['freckles_app_dotfile_folder_name'] = subfolder
            app['freckles_app_profile_name'] = profile_name
            app['freckles_app_dotfile_folder_path'] = dotfiles_dir
            app['freckles_app_dotfile_parent_path'] = subfolder
            app['freckles_app_dotfiles_remote_repo'] = remote_repo
            app['freckles_app_dotfiles_repo_local_dest'] = local_dest
            app['freckles_app_dotfiles_relative_path'] = relative_path

            freckles_metadata_file = os.path.join(dotfiles_dir, FRECKLES_PACKAGE_METADATA_FILENAME)

            if os.path.exists(freckles_metadata_file):
                # have to assume no pyyaml is available
                with open(freckles_metadata_file, "r") as f:
                    data = f.read()
                app[METADATA_CONTENT_KEY] = data

            no_install_file = os.path.join(dotfiles_dir, NO_INSTALL_MARKER_FILENAME)
            if os.path.exists(no_install_file):
                app['freckles_app_no_install'] = True

            no_stow_file = os.path.join(dotfiles_dir, NO_STOW_MARKER_FILENAME)
            if os.path.exists(no_stow_file):
                app['freckles_app_no_stow'] = True

            app_folders.append(app)

        freckles_folders[folder]["apps"] = app_folders

    return freckles_folders


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
                            app[METADATA_CONTENT_KEY] = data
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
                    if data:
                        app[METADATA_CONTENT_KEY] = data
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
            freckles_repos = dict(required=True, type='list'),
            freckles_profiles = dict(default=[], required=False, type='list'),
            freckles_types = dict(required=True, type='list')

        ),
        supports_check_mode=False
    )

    p = module.params

    freckles_repos = p.get('freckles_repos')
    profiles = p.get('freckles_profiles', None)
    freckles_types = p.get('freckles_types')

    dotfile_facts = {}

    freckles_folders = find_freckles_folders(freckles_repos, profiles)
    if 'dotfiles' in freckles_types:
        augment_with_dotfile_packages(freckles_folders)

    # dotfile_packages = create_dotfiles_dict(p['dotfiles_repos'], profiles)
    # dotfile_facts['freckles_dotfile_packages'] = dotfile_packages

    # additional_packages = additional_packages_dict(p['dotfiles_repos'], profiles)
    dotfile_facts['freckles_folders_raw'] = freckles_folders
    # dotfile_facts['freckles_additional_packages'] = additional_packages

    # executable_exists = {}
    # for exe in p.get('executables_to_check', []):
        # missing = missing_from_path(exe)
        # executable_exists[exe] = not missing
    # dotfile_facts['executable_exists'] = executable_exists

    module.exit_json(changed=False, ansible_facts=dict(dotfile_facts))

if __name__ == '__main__':
    main()
