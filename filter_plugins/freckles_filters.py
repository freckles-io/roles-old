#!/usr/bin/python

import copy
import fnmatch
import os
import pprint
import subprocess
from distutils import spawn

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
            'freckles_augment_filter': self.freckles_augment_filter,
            'profile_filter': self.profile_filter
        }


    def process_dotfiles_metadata(self, apps, freckle_parent_folder):

        temp_packages = []
        for app in apps:
            app_name = app['freckles_app_dotfile_folder_name']
            no_install = app.get('freckles_app_no_install', None)
            no_stow = app.get('freckles_app_no_stow', None)

            raw_metadata = app.pop(METADATA_CONTENT_KEY, False)
            if raw_metadata:
                md = yaml.safe_load(raw_metadata)
            else:
                md = {}

            if no_install is not None:
                md["no_install"] = no_install
            if no_stow is not None:
                md["no_stow"] = no_stow

            md["stow_source"] = app['freckles_app_dotfile_folder_path']
            md["stow_folder_name"] = app['freckles_app_dotfile_folder_name']
            md["stow_folder_parent"] = freckle_parent_folder

            temp_packages.append({app_name: md})


        return temp_packages


    def freckles_augment_filter(self, folders_metadata, all_profile_metadata):

        freckles_metadata = {}

        for folder, metadata in folders_metadata.items():

            profile_metadata = all_profile_metadata.get(folder, {})
            freckles_metadata.setdefault(folder, {}).setdefault("vars", metadata.get("vars", {}))

            packages = {"packages": metadata.get("vars", {}).get("packages", [])}

            if "dotfiles" in profile_metadata.keys():
                package_list = self.process_dotfiles_metadata(profile_metadata["dotfiles"], folder)

                if not package_list:
                    package_list = []
                if packages:
                    # if only append, vars will be inherited
                    packages = [[package_list], [{"packages": packages}]]

            # ensuring packages format
            format = {"child_marker": "packages",
                      "default_leaf": "vars",
                      "default_leaf_key": "name",
                      "key_move_map": {'*': "vars"}}
            chain = [frkl.FrklProcessor(format)]
            frkl_obj = frkl.Frkl(packages, chain)
            pkgs = frkl_obj.process()

            freckles_metadata[folder]["vars"]["packages"] = pkgs

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
            folder_vars = frkl_obj.process(frkl.MergeDictResultCallback())

            user_profiles = metadata.get("profiles_to_use", [])
            if user_profiles:
                intersect_profiles = set(folder_vars.get("vars", {}).get("freckle_profiles", []))
                intersect_profiles.intersection(user_profiles)
                folder_vars.setdefault("vars", {})["freckle_profiles"] = list(intersect_profiles)

            result[freckle_folder] = folder_vars
            result[freckle_folder]["meta"] = folders_metadata[freckle_folder]

        return result

    def create_package_list_filter(self, freckles_metadata):

        result = []
        for freckle, freckle_details in freckles_metadata.items():
            apps = freckle_details.get("vars", {}).get("packages", [])
            parent_vars = copy.deepcopy(freckle_details.get("vars", {}))
            parent_vars.pop("packages", None)
            for a in apps:
                # we need to make sure we get all the overlay/parent vars
                temp_app = frkl.dict_merge(parent_vars, a["vars"])
                # result.append({"package": a, "pkg_mgr": profile_pkg_mgr})
                result.append({"vars": temp_app})

        return result

    def profile_filter(self, freckles_metadata):

        profiles = set()

        for freckle, freckle_details in freckles_metadata.items():

            f_profiles = freckle_details.get("vars", {}).get("freckle_profiles")
            if f_profiles:
                profiles.update(f_profiles)

        return list(profiles)


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

    def git_repo_filter(self, freckles):

        if isinstance(freckles, (string_types, dict)):
            freckles = [freckles]
        elif not isinstance(freckles, (list, tuple)):
            raise Exception("Not a valid type for dotfile_repo, can only be dict, string, or a list of one of those: {}".format(freckles))

        result = []
        for fr in freckles:
            if not fr["url"]:
                temp = {"repo": None, "dest": fr["path"]}
            else:
                temp = ensure_git_repo_format(fr["url"], dest=fr["path"])
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
