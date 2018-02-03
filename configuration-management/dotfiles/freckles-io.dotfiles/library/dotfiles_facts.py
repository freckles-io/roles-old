from ansible.module_utils.basic import *
from ansible.module_utils.basic import AnsibleModule

NO_INSTALL_MARKER_FILENAME = ".no_install_freckle"
NO_STOW_MARKER_FILENAME = ".no_stow_freckle"

FRECKLES_FOLDER_MARKER_FILENAME = ".freckle"

METADATA_CONTENT_KEY = "freckle_metadata_file_content"

ROOT_FOLDER_NAME = "__freckles_folder_root__"
DEFAULT_EXCLUDE_DIRS = [".git", ".tox", ".cache"]


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

        app_folders.append(app)

    return app_folders


def main():
    module = AnsibleModule(
        argument_spec=dict(
            freckles_profile_folders=dict(required=True, type='dict')
        ),
        supports_check_mode=False,
    )

    p = module.params

    freckles_folders_metadata = p.get('freckles_profile_folders', None)
    augment_freckles_metadata(module, freckles_folders_metadata)


if __name__ == '__main__':
    main()
