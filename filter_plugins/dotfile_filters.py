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


FRECKLE_METADATA_FILENAME = ".freckles"
NO_INSTALL_MARKER_FILENAME = ".no_install.freckles"
NO_STOW_MARKER_FILENAME = ".no_stow.freckles"

PACKAGES_METADATA_FILENAME = ".packages.freckles"
PROFILE_MARKER_FILENAME = ".profile.freckles"


class FilterModule(object):
    def filters(self):
        return {
            'ensure_list_filter': self.ensure_list_filter,
            'dotfile_repo_format_filter': self.dotfile_repo_format_filter,
            'git_repo_filter': self.git_repo_filter,
            'pkg_mgr_filter': self.pkg_mgr_filter,
            'create_package_list_filter': self.create_package_list_filter,
            'create_additional_packages_list_filter': self.create_package_list_filter
        }

    def create_package_list_filter(self, packages, is_additional_packages_format=False):

        if not is_additional_packages_format:
            for p in packages:
                for pp in p["packages"].keys():
                    #raise Exception(["{} {}".format(key, type(key)) for key in p["packages"][pp].keys()])
                    metadata = p["packages"][pp].pop("freckles_metadata_content", False)

                    if metadata:
                        md = yaml.safe_load(metadata)
                        p["packages"][pp].update(md)
        else:
            for p in packages:
                metadata = p.pop("freckles_metadata_content", False)
                if metadata:
                    md = yaml.safe_load(metadata)
                    p["packages"] = md

        format = {"child_marker": "packages",
                  "default_leaf": "vars",
                  "default_leaf_key": "name",
                  "key_move_map": {'*': "vars"}}
        chain = [frkl.FrklProcessor(format)]

        frkl_obj = frkl.Frkl(packages, chain)
        temp = frkl_obj.process()

        return temp


    def pkg_mgr_filter(self, packages, additional_packages=[], prefix=None):

        temp = copy.copy(packages)
        temp.extend(additional_packages)

        pkg_mgrs = set()

        for p in temp:
            pkg_mgr = p["vars"].get("pkg_mgr", None)
            if pkg_mgr:
                if prefix:
                    pkg_mgr = "{}{}".format(prefix, pkg_mgr)
                pkg_mgrs.add(pkg_mgr)

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
