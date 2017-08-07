#!/usr/bin/python

class FilterModule(object):

    def filters(self):
        return {
            'environment_exists_filter': self.environment_exists_filter
        }

    def environment_exists_filter(self, conda_info):

        pass
