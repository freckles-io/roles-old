#!/usr/bin/python

import copy
import fnmatch
import os
import pprint
import subprocess
from distutils import spawn

from requests.structures import CaseInsensitiveDict
from six import string_types

import yaml
from frkl import frkl
from nsbl.nsbl import ensure_git_repo_format

try:
    set
except NameError:
    from sets import Set as set

METADATA_CONTENT_KEY = "freckles_metadata_content"

class FilterModule(object):
    def filters(self):
        return {
            'ensure_list_filter': self.ensure_list_filter,
            'dotfile_repo_format_filter': self.dotfile_repo_format_filter,
            'git_repo_filter': self.git_repo_filter,
            'pkg_mgr_filter': self.pkg_mgr_filter,
            'create_package_list_filter': self.create_package_list_filter,
            'create_additional_packages_list_filter': self.create_package_list_filter,
            'frklize_folders_metadata_filter': self.frklize_folders_metadata
        }

    def frklize_folders_metadata(self, folders_metadata):

        temp_vars = {}
        packages = {}
        for path, metadata in folders_metadata.items():

            profile = metadata["profile_name"]
            raw_metadata = metadata.get(METADATA_CONTENT_KEY, False)
            if raw_metadata:
                md = yaml.safe_load(raw_metadata)
                # if isinstance(md, (list, tuple)):
                    # md = {"vars": md}
            else:
                md = []

            temp_vars.setdefault(profile, []).append(md)
            packages.setdefault(profile, [])

            apps = metadata["apps"]
            temp_packages = []
            for app in apps:
                app_name = app['freckles_app_dotfile_folder_name']
                no_install = app.get('freckles_app_no_install', None)
                no_stow = app.get('freckles_app_no_stow', None)
                raw_metadata = app.pop(METADATA_CONTENT_KEY, False)
                if raw_metadata:
                    md = yaml.safe_load(raw_metadata)
                    temp_packages.append({app_name: md})
                else:
                    temp_packages.append(app_name)
                if no_install is not None:
                    temp_packages[app_name]["no_install"] = no_install
                if no_stow is not None:
                    temp_packages[app_name]["no_stow"] = no_stow

            packages[profile].append({"packages": temp_packages})

        format = {"child_marker": "childs",
                  "default_leaf": "vars",
                  "default_leaf_key": "name",
                  "key_move_map": {'*': "vars"}}
        chain = [frkl.FrklProcessor(format)]

        result = {}
        # result["_debug"] = temp_vars
        for profile, profile_vars in temp_vars.items():
            frkl_obj = frkl.Frkl(profile_vars, chain)
            result[profile] = frkl_obj.process(frkl.MergeDictResultCallback())

        format = {"child_marker": "packages",
                  "default_leaf": "vars",
                  "default_leaf_key": "name",
                  "key_move_map": {'*': "vars"}}
        chain = [frkl.FrklProcessor(format)]
        for profile, package_list in packages.items():
            profile_packages = result[profile].get("vars", {}).pop("packages", {})
            if profile_packages:
                package_list.append({"packages": profile_packages})
            frkl_obj = frkl.Frkl(package_list, chain)
            pkgs = frkl_obj.process()
            result[profile].setdefault("vars", {})["packages"] = pkgs
            # temp_result.setdefault(profile, {}).setdefault("packages", []) =

        return result

    def create_package_list_filter(self, freckles_profiles):

        result = []
        for profile, profile_details in freckles_profiles.items():
            profile_pkg_mgr = profile_details.get("vars", {}).get("pkg_mgr", "auto")
            apps = profile_details.get("vars", {}).get("packages", [])
            for a in apps:
                result.append({"package": a, "pkg_mgr": profile_pkg_mgr})

        return result


    def pkg_mgr_filter(self, freckles_profiles, prefix=None):

        pkg_mgrs = set()

        for profile, profile_details in freckles_profiles.items():
            profile_pkg_mgr = profile_details.get("vars", {}).get("pkg_mgr", None)
            if profile_pkg_mgr:
                if prefix:
                    profile_pkg_mgr = "{}{}".format(prefix, profile_pkg_mgr)

            at_least_one_app_for_profile_pkg_mgr = False
            for p in profile_details.get("vars", {}).get("packages"):
                no_install = p.get("vars", {}).get("no_install", False)
                if no_install is True:
                    continue
                app_pkg_mgr = p.get("vars", {}).get("pkg_mgr", None)
                if app_pkg_mgr:
                    if prefix:
                        app_pkg_mgr = "{}{}".format(prefix, app_pkg_mgr)
                    pkg_mgrs.add(app_pkg_mgr)
                else:
                    at_least_one_app_for_profile_pkg_mgr = True

            if at_least_one_app_for_profile_pkg_mgr and profile_pkg_mgr:
                pkg_mgrs.add(profile_pkg_mgr)

        return list(pkg_mgrs)

    def ensure_list_filter(self, dotfile_repos):

        if isinstance(dotfile_repos, (string_types, dict)):
            return [dotfile_repos]
        elif isinstance(dotfile_repos, (list, tuple)):
            return dotfile_repos

    def git_repo_filter(self, dotfile_repos):

        if isinstance(dotfile_repos, (string_types, dict)):
            dotfile_repos = [dotfile_repos]
        elif not isinstance(dotfile_repos, (list, tuple)):
            raise Exception("Not a valid type for dotfile_repo, can only be dict, string, or a list of one of those: {}".format(dotfile_repos))

        result = []
        for dr in dotfile_repos:
            temp = ensure_git_repo_format(dr)
            result.append(temp)

        return result

    def dotfile_repo_format_filter(self, dotfile_repos):

        if isinstance(dotfile_repos, (dict, string_types)):
            dotfile_repos = [dotfile_repos]

        temp_repos = []
        for r in dotfile_repos:
            full_repo = ensure_git_repo_format(r)
            temp_repos.append(full_repo)

        #return self.create_dotfiles_dict(temp_repos, profiles)
        return temp_repos
