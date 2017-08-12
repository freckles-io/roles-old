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
            'read_profile_vars_filter': self.read_profile_vars_filter,
            'git_repo_filter': self.git_repo_filter,
            'create_package_list_filter': self.create_package_list_filter,
            'flatten_profiles_filter': self.flatten_profiles_filter,
            'get_used_profile_names': self.get_used_profile_names,
            'create_profile_metadata': self.create_profile_metadata
        }


    def flatten_profiles_filter(self, freckles_metadata):

        temp = {}
        for folder, profiles in freckles_metadata.items():

            for profile, metadata in profiles.items():

                temp.setdefault(profile, {})[folder] = metadata

        # merge metadata
        result = {}
        for profile, folders in temp.items():
            for folder, folder_metadata_list in folders.items():
                metadata = self.create_profile_metadata(folder_metadata_list)
                result.setdefault(profile, {})[folder] = metadata

        return result

    def get_used_profile_names(self, freckles_metadata):

        profile_names = set()

        for folder, profiles in freckles_metadata.items():

            profile_names.update(profiles.keys())

        profile_names.discard(DEFAULT_FRECKLES_PROFILE_NAME)

        return list(profile_names)

    def read_profile_vars_filter(self, folders_metadata):

        temp_vars = {}

        for folder, profiles in folders_metadata.items():

            for profile, metadata in profiles.items():

                raw_metadata = metadata.pop(METADATA_CONTENT_KEY, False)
                if raw_metadata:
                    md = yaml.safe_load(raw_metadata)
                    if not md:
                        md = []
                    # if isinstance(md, (list, tuple)):
                        # md = {"vars": md}
                else:
                    md = []

                temp_vars.setdefault(folder, {}).setdefault(profile, []).append(md)

        result = {}
        for freckle_folder, profiles in temp_vars.items():
            for profile, profile_vars in profiles.items():
                chain = [frkl.FrklProcessor(DEFAULT_PROFILE_VAR_FORMAT)]
                try:
                    frkl_obj = frkl.Frkl(profile_vars, chain)
                    # mdrc_init = {"append_keys": "vars/packages"}
                    # frkl_callback = frkl.MergeDictResultCallback(mdrc_init)
                    frkl_callback = frkl.MergeResultCallback()
                    profile_vars_new = frkl_obj.process(frkl_callback)
                    result.setdefault(freckle_folder, {})[profile] = profile_vars_new
                except (frkl.FrklConfigException) as e:
                    raise errors.AnsibleFilterError(
                        "Can't read freckle metadata file '{}/.{}.freckle': {}".format(freckle_folder, profile, e.message)
)
        return result

    def create_profile_metadata(self, profile_vars):

        result = {}
        chain = [frkl.FrklProcessor(DEFAULT_PROFILE_VAR_FORMAT)]
        try:
            frkl_obj = frkl.Frkl(profile_vars, chain)
            frkl_callback = frkl.MergeDictResultCallback()
            result = frkl_obj.process(frkl_callback)
        except (frkl.FrklConfigException) as e:
            raise errors.AnsibleFilterError("Can't process metadata: {}".format(profile_vars))

        result = result.get("vars", {})
        result.pop("packages", None)
        return result

    def create_package_list_filter(self, freckles_metadata):

        result = []

        for folder, profiles in freckles_metadata.items():
            for profile, var_list in profiles.items():
                for metadata in var_list:

                    parent_vars = copy.deepcopy(metadata.get("vars", {}))
                    parent_vars.pop("packages", None)

                    packages = metadata.get("vars", {}).get("packages", [])

                    pkg_config = {"vars": parent_vars, "packages": packages}

                    chain = [frkl.FrklProcessor(DEFAULT_PACKAGE_FORMAT)]
                    frkl_obj = frkl.Frkl(pkg_config, chain)
                    pkgs = frkl_obj.process()

                    result = result + pkgs

        return sorted(result, key=lambda k: k.get("vars", {}).get("name", "zzz"))

    def git_repo_filter(self, freckles):

        if isinstance(freckles, (string_types, dict)):
            freckles = [freckles]
        elif not isinstance(freckles, (list, tuple)):
            raise Exception("Not a valid type for dotfile_repo, can only be dict, string, or a list of one of those: {}".format(freckles))

        result = []
        # TODO: check valid
        for fr in freckles:
            if "url" not in fr.keys() or not fr["url"]:
                temp = {"repo": None, "dest": fr["path"]}
            else:
                temp = ensure_git_repo_format(fr["url"], dest=fr.get("path", None))
            result.append(temp)

        return result
