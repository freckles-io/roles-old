#!/usr/bin/python

import copy
import os

from frkl import frkl

try:
    set
except NameError:
    from sets import Set as set

METADATA_CONTENT_KEY = "freckle_metadata_file_content"


class FilterModule(object):

    def filters(self):
        return {
            'create_dotfiles_packages': self.create_dotfiles_packages,
            'get_subfolders': self.get_subfolders,
            'create_folder_packages': self.create_folder_packages,
            'create_stow_folders_metadata': self.create_stow_folders_metadata
        }

    def get_subfolders(self, files, base_path):

        subfolders = set()
        for path in files:
            path = path[len(base_path)+1:]
            tokens = path.split(os.path.sep)
            if len(tokens) > 1:
                folder = tokens[0]
            else:
                continue
            subfolders.add(folder)

        return sorted(subfolders)

    def create_folder_packages(self, package_names, extra_vars):

        result = []

        for name in package_names:
            details = {"name": name}
            if name in extra_vars.keys():
                no_install = extra_vars.get(name, {}).get("no_install", False)
                if no_install:
                    continue
                package_md = extra_vars[name].get("package", None)
                if package_md:
                    frkl.dict_merge(details, package_md, copy_dct=False)
            result.append({"vars": details})

        return result

    def create_stow_folders_metadata(self, subfolders, freckle_path, freckle_vars, extra_vars):

        default_stow_target = freckle_vars.get("dotfiles_stow_target", None)
        default_delete_conflicts = freckle_vars.get("dotfiles_stow_delete_conflicts", None)
        default_no_stow = freckle_vars.get("dotfiles_no_stow", None)
        default_stow_become = freckle_vars.get("dotfiles_stow_become", None)

        result = []
        for folder_name in subfolders:

            folder_extra_vars = extra_vars.get(folder_name, {})

            md = {}
            md["stow_folder_name"] = folder_name
            md["stow_folder_parent"] = freckle_path
            if "stow_target_dir" in folder_extra_vars.keys():
                md["stow_target_dir"] = folder_extra_vars["stow_target_dir"]
            elif default_stow_target is not None:
                md["stow_target_dir"] = default_stow_target
            if "stow_delete_conflicts" in folder_extra_vars.keys():
                md["stow_delete_conflicts"] = folder_extra_vars["stow_delete_conflicts"]
            elif default_delete_conflicts is not None:
                md["stow_delete_conflicts"] = dfault_delete_conflicts
            if "no_stow" in folder_extra_vars.keys():
                md["no_stow"] = folder_extra_vars["no_stow"]
            elif default_no_stow is not None:
                md["no_stow"] = default_no_stow
            if "stow_become" in folder_extra_vars.keys():
                md["stow_become"] = folder_extra_vars["stow_become"]
            elif default_stow_become is not None:
                md["stow_become"] = default_stow_become

            result.append(md)

        return result

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
