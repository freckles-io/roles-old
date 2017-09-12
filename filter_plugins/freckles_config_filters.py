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

        return freckles.utils.expand_repos(repos)
