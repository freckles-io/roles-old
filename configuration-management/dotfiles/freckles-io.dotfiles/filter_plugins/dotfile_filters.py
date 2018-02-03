#!/usr/bin/python

import copy

from frkl import frkl
from freckles.freckles_defaults import DEFAULT_PROFILE_VAR_FORMAT, DEFAULT_VAR_FORMAT

try:
    set
except NameError:
    from sets import Set as set

METADATA_CONTENT_KEY = "freckle_metadata_file_content"


class FilterModule(object):
    def filters(self):
        return {
            'create_dotfiles_packages': self.create_dotfiles_packages
        }

    def create_dotfiles_packages(self, profile_vars):

        result = []
        for folder, subfolder_list in profile_vars.items():

            for subfolder_metadata in subfolder_list:

                md = {}
                md["stow_source"] = subfolder_metadata['freckles_app_dotfile_folder_path']
                md["stow_folder_name"] = subfolder_metadata['freckles_app_dotfile_folder_name']
                md["name"] = subfolder_metadata['freckles_app_dotfile_folder_name']
                md["stow_folder_parent"] = subfolder_metadata['freckles_app_dotfile_parent_path']

                parent_details = subfolder_metadata.get('freckles_app_dotfile_parent_details', {})

                extra_vars = copy.deepcopy(parent_details.get("extra_vars", {}).get(md["name"], {}))

                package_md = extra_vars.pop("package", None)
                overlay = frkl.dict_merge(md, extra_vars)
                if package_md:
                    frkl.dict_merge(overlay, package_md, copy_dct=False)

                result.append({"vars": overlay})

        return result
