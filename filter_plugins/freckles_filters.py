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
DEFAULT_FRECKLES_PROFILE_NAME = "__freckles_default__"

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
            'flatten_profiles_filter': self.flatten_profiles_filter,
            'project_name_filter': self.project_name_filter,
            'merge_package_list_filter': self.merge_package_list_filter
        }

    def project_name_filter(self, freckles_path):

        if freckles_path.endswith(os.sep):
            return os.path.basename(freckles_path[0:-1])
        else:
            return os.path.basename(freckles_path)

    def flatten_profiles_filter(self, freckles_metadata):

        result = []
        for folder, profiles in freckles_metadata.items():

            for profile, metadata in profiles.items():

                result.append((profile, folder, metadata))

        return result

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

    def merge_package_list_filter(self, *package_lists):

        temp_packages = []
        for p_list in package_lists:
            if not isinstance(p_list, (list, tuple)):
                temp_packages.append({"packages": [p_list]})
            else:
                temp_packages.append({"packages": p_list})

        # ensuring packages format
        format = {"child_marker": "packages",
                  "default_leaf": "vars",
                  "default_leaf_key": "name",
                  "key_move_map": {'*': "vars"}}
        chain = [frkl.FrklProcessor(format)]
        frkl_obj = frkl.Frkl(temp_packages, chain)
        pkgs = frkl_obj.process()

        return pkgs


    def freckles_augment_filter(self, folders_metadata, all_profile_metadata):

        freckles_metadata = {}

        for folder, profiles in folders_metadata.items():

            for profile, metadata in profiles.items():

                profile_metadata = all_profile_metadata.get(folder, {})
                freckles_metadata.setdefault(folder, {}).setdefault(profile, {}).setdefault("vars", metadata.get("vars", {}))

                profile_metadata_packages = metadata.get("vars", {}).get("packages", [])
                default_packages = {"packages": profile_metadata_packages}

                all_packages = [default_packages]

                if profile == "dotfiles":

                    package_list = self.process_dotfiles_metadata(profile_metadata["dotfiles"], folder)

                    if package_list:
                        all_packages.append(package_list)

                # ensuring packages format
                pkgs = self.merge_package_list_filter(*all_packages)

                freckles_metadata[folder][profile]["vars"]["packages"] = pkgs

        return freckles_metadata

    def frklize_folders_metadata(self, folders_metadata):

        temp_vars = {}

        for folder, profiles in folders_metadata.items():

            for profile, metadata in profiles.items():

                raw_metadata = metadata.get(METADATA_CONTENT_KEY, False)
                if raw_metadata:
                    md = yaml.safe_load(raw_metadata)
                    if not md:
                        md = []
                    # if isinstance(md, (list, tuple)):
                        # md = {"vars": md}
                else:
                    md = []

                temp_vars.setdefault(folder, {}).setdefault(profile, []).append(md)

        format = {"child_marker": "childs",
                  "default_leaf": "vars",
                  "default_leaf_key": "name",
                  "key_move_map": {'*': "vars"}}

        result = {}
        for freckle_folder, profiles in temp_vars.items():
            for profile, profile_vars in profiles.items():
                chain = [frkl.FrklProcessor(format)]
                frkl_obj = frkl.Frkl(profile_vars, chain)
                profile_vars_new = frkl_obj.process(frkl.MergeDictResultCallback())

                result.setdefault(freckle_folder, {})[profile] = {"vars": profile_vars_new.get("vars", {}), "meta": folders_metadata[freckle_folder][profile]}

        return result

    def create_package_list_filter(self, freckles_metadata):

        result = []
        for folder, profiles in freckles_metadata.items():
            for profile, metadata in profiles.items():
                apps = metadata.get("vars", {}).get("packages", [])
                parent_vars = copy.deepcopy(metadata.get("vars", {}))
                parent_vars.pop("packages", None)
                for a in apps:
                    # we need to make sure we get all the overlay/parent vars
                    temp_app = frkl.dict_merge(parent_vars, a["vars"])
                    # result.append({"package": a, "pkg_mgr": profile_pkg_mgr})
                    # pkg_mgr = temp_app.get("pkg_mgr", "auto")
                    result.append({"vars": temp_app})

        return sorted(result, key=lambda k: k.get("vars", {}).get("name", "zzz"))


    def pkg_mgr_filter(self, freckles_metadata, prefix=None):

        pkg_mgrs = set()

        for folder, profiles in freckles_metadata.items():

            for profile, metadata in profiles.items():

                for package in metadata.get("vars", {}).get("packages", []):
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
