import fnmatch

from ansible.module_utils.basic import *
from ansible.module_utils.basic import AnsibleModule

FRECKLES_PACKAGE_METADATA_FILENAME = ".package_freckle"
NO_INSTALL_MARKER_FILENAME = ".no_install_freckle"
NO_STOW_MARKER_FILENAME = ".no_stow_freckle"

FRECKLES_FOLDER_MARKER_FILENAME = ".freckle"
FRECKLES_IGNORE_FOLDER_MARKER_FILENAME = ".ignore.freckle"

METADATA_CONTENT_KEY = "freckle_metadata_file_content"

ROOT_FOLDER_NAME = "__freckles_folder_root__"
DEFAULT_EXCLUDE_DIRS = [".git", ".tox", ".cache"]


def find_freckles_folders(module, freckles_repos):
    """Walks through all the provided dotfiles, and creates a dictionary with values according to what it finds, per folder.

    Args:
      freckles_repos (list): a list of dotfile dictionaries (see: XXX)
    """

    freckles_paths_all = []
    for r in freckles_repos:

        repo_id = r["id"]
        repo_priority = r["priority"]
        local_parent = r["local_parent"]
        local_name = r["local_name"]

        root_path = os.path.expanduser(os.path.join(local_parent, local_name))

        remote_url = r.get("remote_url", None)

        include = r.get("include", None)
        exclude = r.get("exclude", None)

        non_recursive = r["non_recursive"]
        add_file_list = r.get("add_file_list", True)

        freckles_paths = []

        ignore_paths = []

        # find all .ignore.freckle files
        for root, dirnames, filenames in os.walk(root_path, topdown=True):
            dirnames[:] = [d for d in dirnames if d not in DEFAULT_EXCLUDE_DIRS]

            # check for .freckles profiles
            for filename in fnmatch.filter(filenames, FRECKLES_IGNORE_FOLDER_MARKER_FILENAME):

                folder_name = os.path.basename(root)
                local_path = os.path.join(os.path.expanduser(root_path), root)
                ignore_paths.append(local_path)

        # find all freckles folders
        for root, dirnames, filenames in os.walk(root_path, topdown=True):
            dirnames[:] = [d for d in dirnames if d not in DEFAULT_EXCLUDE_DIRS]

            # check for .freckles profiles
            for filename in fnmatch.filter(filenames, FRECKLES_FOLDER_MARKER_FILENAME):

                # check whether we only should consider certain folders
                if include:
                    match = False
                    for token in include:
                        if root.endswith(token):
                            match = True
                            break

                    if not match:
                        continue

                if exclude:
                    match = False
                    for token in exclude:
                        if root.endswith(token):
                            match = True
                            break

                    if match:
                        continue

                folder_name = os.path.basename(root)
                local_path = os.path.join(os.path.expanduser(root_path), root)

                ignore = False
                for ip in ignore_paths:
                    if local_path.startswith(ip):
                        ignore = True
                        break

                if os.path.abspath(local_path) != os.path.abspath(root_path):
                    if non_recursive:
                        continue
                    else:
                        is_base_folder = False
                else:
                    is_base_folder = True

                if ignore:
                    continue

                path_metadata = {}

                path_metadata["folder_name"] = folder_name
                path_metadata["is_base_folder"] = is_base_folder
                path_metadata["remote_repo"] = remote_url
                # path_metadata["repo_local_dest"] = root_path
                path_metadata["parent_repo_path"] = root_path
                path_metadata["parent_repo_id"] = repo_id
                path_metadata["repo_priority"] = repo_priority
                rel_path = os.path.relpath(root, root_path)
                path_metadata["relative_path"] = rel_path
                if rel_path != ".":
                    path_metadata["full_path"] = os.path.join(root_path, rel_path)
                else:
                    path_metadata["full_path"] = root_path

                metadata_file = os.path.join(local_path, filename)

                if os.path.exists(metadata_file):
                    with open(metadata_file, "r") as f:
                        data = f.read()
                    if not data:
                        data = ""
                else:
                    data = ""

                # don't use any templates in here, it'd just be super confusing
                # TODO: add those, but make sure it doesn't interfere
                if "{{"  not in metadata_file and "{{" not in data:
                    path_metadata[METADATA_CONTENT_KEY] = data

                path_metadata["extra_vars"] = {}
                path_metadata["files"] = []

                for sub_root, sub_dirnames, sub_filenames in os.walk(root, topdown=True):

                    sub_dirnames[:] = [sd for sd in sub_dirnames if sd not in DEFAULT_EXCLUDE_DIRS]

                    if add_file_list:
                        path_metadata["files"].extend([os.path.join(sub_root, f).replace("{{", "\{\{").replace("}}", "\}\}") for f in sub_filenames])
                    # check for .freckles profiles
                    for sub_filename in fnmatch.filter(sub_filenames, "*{}".format(FRECKLES_FOLDER_MARKER_FILENAME)):

                        sub_metadata_file = os.path.join(sub_root, sub_filename)
                        sub_metadata_path = os.path.relpath(sub_metadata_file, root)

                        if not sub_filename.startswith(".") or sub_filename == FRECKLES_FOLDER_MARKER_FILENAME:
                            continue

                        with open(sub_metadata_file, "r") as f:
                            data = f.read()
                        # we can't use anything that has jinja2 template in them, as it'll confuse things
                        #TODO: log output for this case
                        if not data:
                            data = ""

                        if '{{' in data or "{{" in sub_metadata_file:
                            continue

                        path_metadata["extra_vars"][sub_metadata_path] = data
                freckles_paths.append(path_metadata)

        if freckles_paths:
            freckles_paths_all.extend(freckles_paths)
        else:
            # we assume the root folder is a freckle
            root = root_path
            folder_name = os.path.basename(root)
            local_path = root
            path_metadata = {}
            path_metadata["folder_name"] = folder_name
            path_metadata["is_base_folder"] = True
            path_metadata["remote_repo"] = remote_url
            # path_metadata["repo_local_dest"] = root_path
            path_metadata["parent_repo_path"] = root_path
            path_metadata["parent_repo_id"] = repo_id
            path_metadata["repo_priority"] = repo_priority
            rel_path = os.path.relpath(root, root_path)
            path_metadata["relative_path"] = rel_path
            if rel_path != ".":
                path_metadata["full_path"] = os.path.join(root_path, rel_path)
            else:
                path_metadata["full_path"] = root_path

            metadata_file = os.path.join(root, FRECKLES_FOLDER_MARKER_FILENAME)

            if os.path.exists(metadata_file):
                with open(metadata_file, "r") as f:
                    data = f.read()
                if not data:
                    data = ""
            else:
                data = ""

            # don't use any templates in here, it'd just be super confusing
            if "{{"  not in metadata_file and "{{" not in data:
                path_metadata[METADATA_CONTENT_KEY] = data

            path_metadata["extra_vars"] = {}
            path_metadata["files"] = []

            for sub_root, sub_dirnames, sub_filenames in os.walk(root, topdown=True):

                sub_dirnames[:] = [sd for sd in sub_dirnames if sd not in DEFAULT_EXCLUDE_DIRS]
                if add_file_list:
                    path_metadata["files"].extend([os.path.join(sub_root, f).replace("{{", "\{\{").replace("}}", "\}\}") for f in sub_filenames])

                # check for .freckles profiles
                for sub_filename in fnmatch.filter(sub_filenames, "*{}".format(FRECKLES_FOLDER_MARKER_FILENAME)):

                    sub_metadata_file = os.path.join(sub_root, sub_filename)
                    sub_metadata_path = os.path.relpath(sub_metadata_file, root)

                    if not sub_filename.startswith(".") or sub_filename == FRECKLES_FOLDER_MARKER_FILENAME:
                        continue

                    with open(sub_metadata_file, "r") as f:
                        data = f.read()
                    if not data:
                        data = ""

                    if '{{' in data or '{{' in sub_filename:
                        continue

                    path_metadata["extra_vars"][sub_metadata_path] = data

            freckles_paths_all.append(path_metadata)

    return freckles_paths_all


# def get_subfolder_metadata(folder, folder_details):
#     """Walks through provided freckles folders, assumes every sub-folder is a folder representing an app.

#     If such a sub-folder contains a file called .package.freckles, tihs will be read and the (yaml) data in it will be super-imposed on top of the freckles_folder metadata.
#     """

#     app_folders = []
#     for subfolder in os.listdir(folder):

#         dotfiles_dir = os.path.join(folder, subfolder)
#         if subfolder.startswith(".") or not os.path.isdir(dotfiles_dir):
#             continue

#         app = {}
#         app['freckles_app_dotfile_folder_name'] = subfolder
#         app['freckles_app_dotfile_folder_path'] = dotfiles_dir
#         app['freckles_app_dotfile_parent_path'] = folder
#         app['freckles_app_dotfile_parent_details'] = folder_details

#         freckles_metadata_file = os.path.join(dotfiles_dir, FRECKLES_PACKAGE_METADATA_FILENAME)

#         if os.path.exists(freckles_metadata_file):
#             # have to assume no pyyaml is available
#             with open(freckles_metadata_file, "r") as f:
#                 data = f.read()
#             app[METADATA_CONTENT_KEY] = data

#         no_install_file = os.path.join(dotfiles_dir, NO_INSTALL_MARKER_FILENAME)
#         if os.path.exists(no_install_file):
#             app['freckles_app_no_install'] = True

#         no_stow_file = os.path.join(dotfiles_dir, NO_STOW_MARKER_FILENAME)
#         if os.path.exists(no_stow_file):
#             app['freckles_app_no_stow'] = True

#         app_folders.append(app)

#     return app_folders

def main():
    module = AnsibleModule(
        argument_spec=dict(
            freckles_repos=dict(required=True, type='list'),
        ),
        supports_check_mode=False
    )

    p = module.params

    freckles_repos = p.get('freckles_repos', None)

    freckles_paths = find_freckles_folders(module, freckles_repos)
    freckles_facts = {}
    freckles_facts['freckles_folders_raw'] = freckles_paths
    module.exit_json(changed=False, ansible_facts=dict(freckles_facts))


if __name__ == '__main__':
    main()
