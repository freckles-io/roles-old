#!/usr/bin/python

import copy
import re
from collections import OrderedDict
import os
import yaml
from ansible import errors
from frkl import frkl
from nsbl.nsbl import ensure_git_repo_format
from six import string_types
from freckles.freckles_defaults import DEFAULT_PROFILE_VAR_FORMAT, DEFAULT_VAR_FORMAT, DEFAULT_PACKAGE_FORMAT
from freckles.utils import render_dict

try:
    set
except NameError:
    from sets import Set as set


class FilterModule(object):
    def filters(self):
        return {
            'create_extra_pkg_mgrs_list': self.create_extra_pkg_mgrs_list,
            'create_package_list_from_profiles_metadata': self.create_package_list_from_profiles_metadata,
            'flatten_profile_vars': self.flatten_profile_vars,
            'resolve_paths': self.resolve_paths,
            'check_become': self.check_become
        }

    def check_become(self, folder_metadata_list):

        for md in folder_metadata_list:
            become = md["checkout_become"]

            if become:
                return True

        return False

    def resolve_paths(self, folder_metadata_list, home_dir):

        for md in folder_metadata_list:
            path = md["local_parent"]

            if path.startswith("~/"):
                path_new = os.path.join(home_dir, path[2:])
                md["local_parent"] = path_new

        return folder_metadata_list

    def flatten_profile_vars(self, profile_folder_list):

        if not profile_folder_list:
            return {}

        result = {}
        for f in profile_folder_list:
            frkl.dict_merge(result, f["vars"], copy_dct=False)

        return result

    def create_extra_pkg_mgrs_list(self, freckelize_profiles_metadata):

        extra_pkg_mgrs = set()

        for profile, folder_list in freckelize_profiles_metadata.items():

            for folder_metadata in folder_list:
                extras = folder_metadata["vars"].get("pkg_mgrs", [])
                extra_pkg_mgrs.update(extras)

        return list(extra_pkg_mgrs)

    def create_package_list_from_profiles_metadata(self, freckelize_profiles_metadata, default_pkg_mgr):
        """
        Tries to get all packages from all freckle items.
        """

        result = []

        for profile, folder_list in freckelize_profiles_metadata.items():

            for folder_metadata in folder_list:
                packages = folder_metadata["folder_vars"].get("install", [])
                if not packages:
                    continue

                parent_vars = copy.deepcopy(folder_metadata["vars"])
                parent_vars.pop("install", None)

                if "pkg_mgr" not in parent_vars.keys():
                    parent_vars["pkg_mgr"] = default_pkg_mgr
                pkg_config = {"vars": parent_vars, "packages": packages}

                chain = [frkl.FrklProcessor(DEFAULT_PACKAGE_FORMAT)]
                frkl_obj = frkl.Frkl(pkg_config, chain)
                pkgs = frkl_obj.process()

                result = result + pkgs

        # TODO: remove duplicates?
        #return sorted(result, key=lambda k: k.get("vars", {}).get("name", "zzz"))
        return result
