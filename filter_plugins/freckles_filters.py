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

DEFAULT_PROFILE_VAR_FORMAT = {"child_marker": "profiles",
                              "default_leaf": "profile",
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
            'create_package_list_from_var_filter': self.create_package_list_from_var_filter,
            'extra_pkg_mgrs_filter': self.extra_pkg_mgrs_filter,
            'flatten_profiles_filter': self.flatten_profiles_filter,
            # 'get_used_profile_names': self.get_used_profile_names,
            # 'create_profile_metadata': self.create_profile_metadata
        }


    def flatten_profiles_filter(self, freckles_metadata):

        temp = {}
        profiles_available = set()
        for folder, all_vars in freckles_metadata.items():

            extra_vars = all_vars["extra_vars"]
            for metadata in all_vars["vars"]:

                profile_md = metadata.pop("profile")
                profile = profile_md["name"]
                profiles_available.add(profile)

                temp.setdefault(profile, {}).setdefault(folder, {}).setdefault("vars", []).append(metadata)
                temp[profile][folder]["extra_vars"] = extra_vars

        profiles_available = list(profiles_available)

        profiles_to_run = {}
        for profile, folder_vars in temp.items():

            for folder, f_vars in folder_vars.items():

                profiles_to_use = freckles_metadata[folder]["folder_metadata"]["profiles_to_use"]

                if not profiles_to_use:
                    # means we run all the available profiles, except the 'freckle' one
                    if profile != "freckle":
                        profiles_to_run.setdefault(profile, {})[folder] = f_vars

                else:
                    if profile in profiles_to_use:
                        profiles_to_run.setdefault(profile, {}).setdefault(folder, {}).setdefault("vars", []).extend(f_vars.get("vars", []))
                    elif profile == "freckle":
                        for ptr in profiles_to_use:
                            profiles_to_run.setdefault(ptr, {}).setdefault(folder, {}).setdefault("vars", [])
                            for f_var_item in f_vars.get("vars", []):
                                t = f_var_item.get("vars", None)
                                if t:
                                    profiles_to_run[ptr][folder]["vars"].append({"vars": t})

                            profiles_to_run[ptr][folder]["extra_vars"] = f_vars["extra_vars"]

        return profiles_to_run

    # def get_used_profile_names(self, freckles_metadata):

    #     profile_names = set()

    #     for folder, profiles in freckles_metadata.items():

    #         profile_names.update(profiles.keys())

    #     profile_names.discard(DEFAULT_FRECKLES_PROFILE_NAME)

    #     return list(profile_names)

    def read_profile_vars_filter(self, folders_metadata):

        temp_vars = {}
        extra_vars = {}

        for folder, metadata in folders_metadata.items():

            raw_metadata = metadata.pop(METADATA_CONTENT_KEY, False)
            if raw_metadata:
                md = yaml.safe_load(raw_metadata)
                if not md:
                    md = []
                # if isinstance(md, (list, tuple)):
                    # md = {"vars": md}
            else:
                md = [{"profile": {"name": "freckle"}, "vars": {}}]

            temp_vars.setdefault(folder, []).append(md)

            extra_vars_raw = metadata.pop("extra_vars", False)
            if extra_vars_raw:
                for rel_path, extra_metadata_raw in extra_vars_raw.items():
                    extra_metadata = yaml.safe_load(extra_metadata_raw)
                    if not extra_metadata:
                        # this means there was an empty file. We interprete that as setting a flag to true
                        extra_metadata = True

                    sub_path, filename = os.path.split(rel_path)
                    extra_vars.setdefault(folder, {}).setdefault(sub_path, {})[filename[1:-8]] = extra_metadata

        result = {}
        for freckle_folder, metadata_list in temp_vars.items():

            chain = [frkl.FrklProcessor(DEFAULT_PROFILE_VAR_FORMAT)]
            try:
                frkl_obj = frkl.Frkl(metadata_list, chain)
                # mdrc_init = {"append_keys": "vars/packages"}
                # frkl_callback = frkl.MergeDictResultCallback(mdrc_init)
                frkl_callback = frkl.MergeResultCallback()
                profile_vars_new = frkl_obj.process(frkl_callback)
                result.setdefault(freckle_folder, {})["vars"] = profile_vars_new
                result[freckle_folder]["extra_vars"] = extra_vars.get(freckle_folder, {})
                result[freckle_folder]["folder_metadata"] = folders_metadata[freckle_folder]
            except (frkl.FrklConfigException) as e:
                raise errors.AnsibleFilterError(
                    "Can't read freckle metadata file '{}/.freckle': {}".format(freckle_folder, e.message))
        return result

    def create_package_list_from_var_filter(self, packages_key, parent_vars):

        parent_vars_copy = copy.deepcopy(parent_vars.get("vars", {}))
        package_list = parent_vars_copy.pop(packages_key, [])

        pkg_config = {"vars": parent_vars_copy, "packages": package_list}

        chain = [frkl.FrklProcessor(DEFAULT_PACKAGE_FORMAT)]
        frkl_obj = frkl.Frkl(pkg_config, chain)
        pkgs = frkl_obj.process()

        return sorted(pkgs, key=lambda k: k.get("vars", {}).get("name", "zzz"))


    def extra_pkg_mgrs_filter(self, freckles_profile_metadata):

        extra_pkg_mgrs = set()

        for folder, folder_metadata in freckles_profile_metadata.items():

            var_list = folder_metadata.get("vars", [])
            for metadata in var_list:

                extras = metadata.get("vars", {}).get("pkg_mgrs", [])
                extra_pkg_mgrs.update(extras)

        return list(extra_pkg_mgrs)


    def create_package_list_filter(self, freckles_profile_metadata):

        result = []

        for folder, folder_metadata in freckles_profile_metadata.items():

            var_list = folder_metadata.get("vars", [])
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
