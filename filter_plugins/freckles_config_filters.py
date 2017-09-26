#!/usr/bin/python

import os

from  freckles import utils, config, freckles_defaults
from frkl import frkl
from ansible import errors

class FilterModule(object):
    def filters(self):
        return {
            'expand_repos_filter': self.expand_repos_filter,
            'freckles_config_read': self.freckles_config_read
        }

    def freckles_config_read(self, path):

        config_file = os.path.join(path, freckles_defaults.FRECKLE_MARKER_FILE_NAME)

        if not os.path.exists(config_file):
            return {}

        try:
            result = config.parse_config_file(config_file)
        except (frkl.FrklConfigException) as e:
            raise errors.AnsibleFilterError(
                "Can't read freckle metadata file '{}': {}".format(path, e.message))

        return result

    def expand_repos_filter(self, repos):
        result = utils.expand_repos(repos)
        return result
