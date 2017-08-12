import fnmatch
import os

from ansible.module_utils.basic import *
from ansible.module_utils.basic import AnsibleModule

FRECKLES_PACKAGE_METADATA_FILENAME = ".package_freckle"
NO_INSTALL_MARKER_FILENAME = ".no_install_freckle"
NO_STOW_MARKER_FILENAME = ".no_stow_freckle"

FRECKLES_FOLDER_MARKER_FILENAME = ".freckle"

METADATA_CONTENT_KEY = "freckle_metadata_file_content"

ROOT_FOLDER_NAME = "__freckles_folder_root__"
DEFAULT_EXCLUDE_DIRS = [".git", ".tox", ".cache"]

DEFAULT_FRECKLES_PROFILE_NAME = "__freckles_default__"

def augment_freckles_metadata(module, freckles_folders_metadata):
    """Augments metadata using profile-specific lookups."""

    result = {}
    for folder, metadata in freckles_folders_metadata.items():

        result_md = get_dotfiles_metadata(folder, metadata)
        result[folder] = result_md

    freckles_profiles_facts = {}
    freckles_profiles_facts['freckles_profile_dotfiles_metadata'] = result
    module.exit_json(changed=False, ansible_facts=dict(freckles_profiles_facts))


def get_dotfiles_metadata(folder, folder_details):
    """Walks through provided freckles folders, assumes every sub-folder is a folder representing an app.

    If such a sub-folder contains a file called .package.freckles, tihs will be read and the (yaml) data in it will be super-imposed on top of the freckles_folder metadata.
    """

    app_folders = []
    for subfolder in os.listdir(folder):

        dotfiles_dir = os.path.join(folder, subfolder)
        if subfolder.startswith(".") or not os.path.isdir(dotfiles_dir):
            continue

        app = {}
        app['freckles_app_dotfile_folder_name'] = subfolder
        app['freckles_app_dotfile_folder_path'] = dotfiles_dir
        app['freckles_app_dotfile_parent_path'] = folder
        app['freckles_app_dotfile_parent_details'] = folder_details

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

    return app_folders

def main():
    module = AnsibleModule(
        argument_spec = dict(
            freckles_profile_folders = dict(required=True, type='dict')
        ),
        supports_check_mode=False,
    )

    p = module.params

    freckles_folders_metadata = p.get('freckles_profile_folders', None)
    augment_freckles_metadata(module, freckles_folders_metadata)


if __name__ == '__main__':
    main()
