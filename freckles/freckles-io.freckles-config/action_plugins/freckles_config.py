from __future__ import absolute_import, division, print_function

from ansible import constants as C
from ansible.plugins.action import ActionBase

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

FRECKLE_MARKER_FILE_NAME = ".freckle"

class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):

        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)

        config_tasks = self._task.args.get('freckles_config_tasks')

        config_folder = os.path.join(os.path.expanduser("~"), ".freckles")
        if not os.path.exists(config_folder):
            os.makedirs(config_folder)

        config_file = os.path.join(config_folder, FRECKLE_MARKER_FILE_NAME)
        if os.path.exists(config_file):
            with open(config_file) as f:
                old_config = yaml.safe_load(f)
        else:
            old_config = {}

        # defaults
        if "trusted-repos" not in old_config.keys():
            old_config["trusted-repos"] = ["default", "user"]

        if "enable_repos" in config_tasks.keys():
            self.enable_repos(old_config, config_tasks["enable_repos"])

        if "disable_repos" in config_tasks.keys():
            self.disable_repos(old_config, config_tasks["disable_repos"])

        with open(config_file, 'w') as f:
            yaml.safe_dump(old_config, f, default_flow_style=False, allow_unicode=True, encoding="utf-8")

        result["ansible_facts"] = dict({"freckles_file_config": old_config})
        return result

    def enable_repos(self, old_config, repos):

        trusted_repos = old_config.get("trusted-repos", [])

        for repo in repos:
            if not repo in trusted_repos:
                trusted_repos.append(repo)

        old_config["trusted-repos"] = trusted_repos

    def disable_repos(self, old_config, repos):

        trusted_repos = old_config.get("trusted-repos", [])

        for repo in repos:
            if repo in trusted_repos:
                while repo in trusted_repos: trusted_repos.remove(repo)

        old_config["trusted-repos"] = trusted_repos


if __name__ == '__main__':
    main()
