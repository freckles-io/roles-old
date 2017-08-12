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

SUPPORTED_ROLE_PACKAGES = {
    "vagrant": "makkus.install-vagrant"
}

class FilterModule(object):
    def filters(self):
        return {
            'pkg_mgr_filter': self.pkg_mgr_filter
        }


    def pkg_mgr_filter(self, package_list, prefix=None):

        pkg_mgrs = set()

        for pkg in package_list:
            pkg_mgr = pkg.get("vars", {}).get("pkg_mgr", None)
            if pkg_mgr and not pkg_mgr == "auto" and not pkg_mgr == "ansible_role":
                pkg_mgrs.add(pkg_mgr)

        if prefix:
            return ["{}{}".format(prefix, item) for item in pkg_mgrs]
        else:
            return list(pkg_mgrs)
