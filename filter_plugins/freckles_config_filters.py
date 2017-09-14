#!/usr/bin/python

import freckles

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
