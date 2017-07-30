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
            'frklize_folders_metadata_filter': self.frklize_folders_metadata,
            'freckles_augment_filter': self.freckles_augment_filter
        }


    def process_dotfiles_metadata(self, apps):

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

        return temp_packages


    def freckles_augment_filter(self, folders_metadata, all_profile_metadata):

        freckles_metadata = {}

        for folder, metadata in folders_metadata.items():

            profile_metadata = all_profile_metadata.get(folder, {})
            freckles_metadata.setdefault(folder, {}).setdefault("vars", metadata.get("vars", {}))
            if not profile_metadata:
                continue

            if "dotfiles" in profile_metadata.keys():
                profile_packages = metadata.get("vars", {}).get("packages", {})
                package_list = self.process_dotfiles_metadata(profile_metadata["dotfiles"])
                if not package_list:
                    package_list = []
                if profile_packages:
                    # if only append, vars will be inherited
                    package_list = [[package_list], [{"packages": profile_packages}]]

                format = {"child_marker": "packages",
                          "default_leaf": "vars",
                          "default_leaf_key": "name",
                          "key_move_map": {'*': "vars"}}
                chain = [frkl.FrklProcessor(format)]
                frkl_obj = frkl.Frkl(package_list, chain)
                pkgs = frkl_obj.process()

                freckles_metadata[folder]["vars"]["packages"] = pkgs
                # metadata.setdefault("vars", {})["packages"] = pkgs
                    # temp_result.setdefault(profile, {}).setdefault("packages", []) =

        return freckles_metadata

    def frklize_folders_metadata(self, folders_metadata):

        temp_vars = {}

        for folder, metadata in folders_metadata.items():

            raw_metadata = metadata.get(METADATA_CONTENT_KEY, False)
            if raw_metadata:
                md = yaml.safe_load(raw_metadata)
                if not md:
                    md = []
                # if isinstance(md, (list, tuple)):
                    # md = {"vars": md}
            else:
                md = []

            temp_vars.setdefault(folder, []).append(md)

        format = {"child_marker": "childs",
                  "default_leaf": "vars",
                  "default_leaf_key": "name",
                  "key_move_map": {'*': "vars"}}

        result = {}
        for freckle_folder, freckle_vars in temp_vars.items():
            chain = [frkl.FrklProcessor(format)]
            frkl_obj = frkl.Frkl(freckle_vars, chain)
            result[freckle_folder] = frkl_obj.process(frkl.MergeDictResultCallback())
            result[freckle_folder]["meta"] = folders_metadata[freckle_folder]

        return result

    def create_package_list_filter(self, freckles_profiles):

        result = []
        for profile, profile_details in freckles_profiles.items():
            profile_pkg_mgr = profile_details.get("vars", {}).get("pkg_mgr", "auto")
            apps = profile_details.get("vars", {}).get("packages", [])
            parent_vars = copy.deepcopy(profile_details.get("vars", {}))
            parent_vars.pop("packages", None)
            for a in apps:
                # we need to make sure we get all the overlay/parent vars
                temp_app = frkl.dict_merge(parent_vars, a["vars"])
                # result.append({"package": a, "pkg_mgr": profile_pkg_mgr})
                result.append({"vars": temp_app})

        return result


    def pkg_mgr_filter(self, freckles_packages, prefix=None):

        pkg_mgrs = set()

        for package in freckles_packages:

            pkg_mgr = package.get("vars", {}).get("pkg_mgr", None)
            if pkg_mgr:
                pkg_mgrs.add(pkg_mgr)

        if prefix:
            return ["{}{}".format(prefix, item) for item in pkg_mgrs]
        else:
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
