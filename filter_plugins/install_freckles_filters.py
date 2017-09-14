#!/usr/bin/python

class FilterModule(object):
    def filters(self):
        return {
            'environment_exists_filter': self.environment_exists_filter
        }

    def environment_exists_filter(self, conda_info, conda_environment):
        envs = conda_info.get("envs", [])

        return any([e.endswith(conda_environment) for e in envs])
