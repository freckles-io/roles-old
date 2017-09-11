#!/usr/bin/python

import re
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
import freckles

import yaml

try:
    set
except NameError:
    from sets import Set as set

class FilterModule(object):

    def filters(self):
        return {
            'expand_repos_filter': self.expand_repos_filter,
        }


    def expand_repos_filter(self, repos):

        result = []
        for repo in repos:
            fields = ["url", "path"]
            r = freckles.freckles_defaults.get_repo(repo)
            role_tuples = r.get("roles", [])
            if role_tuples:
                temp = [dict(zip(fields, t)) for t in role_tuples]
                result.extend(temp)
            adapter_tuples = r.get("adapters", [])
            if adapter_tuples:
                temp = [dict(zip(fields, t)) for t in adapter_tuples]
                result.extend(temp)
            frecklecutable_tuples = r.get("frecklecutables", [])
            if frecklecutable_tuples:
                temp = [dict(zip(fields, t)) for t in frecklecutable_tuples]
                result.extend(temp)

        return result
