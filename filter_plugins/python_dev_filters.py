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

class FilterModule(object):
    def filters(self):
        return {
            'project_name_filter': self.project_name_filter
        }

    def project_name_filter(self, project_path):

        return os.path.basename(project_path)
