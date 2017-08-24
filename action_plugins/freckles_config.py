from __future__ import absolute_import, division, print_function

import os
import pprint
import sys

from ansible import constants as C
from ansible.errors import AnsibleError, AnsibleFileNotFound
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.plugins.action import ActionBase
from ansible.template import generate_ansible_template_vars
from ansible.utils.hashing import checksum_s

from six import string_types
try:
    set
except NameError:
    from sets import Set as set

__metaclass__ = type

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

boolean = C.mk_boolean

import os
import yaml

from frkl.frkl import dict_merge

class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):

        if task_vars is None:
             task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)

        config_tasks = self._task.args.get('freckles_config_tasks')

        config_file = os.path.join(os.path.expanduser("~"), ".freckles", 'config.yml')
        if os.path.exists(config_file):
            with open(config_file) as f:
                old_config = yaml.safe_load(f)
        else:
            old_config = {}

        if "enable_community_repo" in config_tasks:
            self.enable_community_repo(old_config, enable=True)
        elif "disable_community_repo" in config_tasks:
            self.enable_community_repo(old_config, enable=False)

        with open(config_file, 'w') as f:
            yaml.dump(old_config, f, default_flow_style=False)

        return result

    def enable_community_repo(self, old_config, enable=True):

        trusted_repos = old_config.get("trusted-repos", ["default", "user"])

        if not "community" in trusted_repos:
            if enable:
                trusted_repos.append("community")
        else:
            if not enable:
                while "community" in trusted_repos: trusted_repos.remove("community")

        old_config["trusted-repos"] = trusted_repos

        trusted_profiles = old_config.get("trusted-profiles", ["default", "user"])

        if not "community" in trusted_profiles:
            if enable:
                trusted_profiles.append("community")
        else:
            if not enable:
                while "community" in trusted_profiles: trusted_profiles.remove("community")

        old_config["trusted-profiles"] = trusted_profiles

        return



if __name__ == '__main__':
    main()
