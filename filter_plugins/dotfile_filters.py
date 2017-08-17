#!/usr/bin/python

import copy
import fnmatch
import os
import pprint
import subprocess
from distutils import spawn

from ansible import errors
from frkl import frkl
from nsbl.nsbl import ensure_git_repo_format
from requests.structures import CaseInsensitiveDict
from six import string_types

import yaml

try:
    set
except NameError:
    from sets import Set as set

METADATA_CONTENT_KEY = "freckle_metadata_file_content"
DEFAULT_FRECKLES_PROFILE_NAME = "__freckles_default__"

SUPPORTED_ROLE_PACKAGES = {
    "vagrant": "makkus.install-vagrant"
}

DEFAULT_PROFILE_VAR_FORMAT = {"child_marker": "childs",
                              "default_leaf": "vars",
                              "default_leaf_key": "name",
                              "key_move_map": {'*': "vars"}}

DEFAULT_PACKAGE_FORMAT = {"child_marker": "packages",
                          "default_leaf": "vars",
                          "default_leaf_key": "name",
                          "key_move_map": {'*': "vars"}}

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
