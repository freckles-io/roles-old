#!/usr/bin/python

PKG_MGRS_EXECUTABLES_MAP = {
    "git": "git",
    "nix": "nix-env",
    "conda": "conda",
    "homebrew": "brew"
}

class FilterModule(object):

    def filters(self):
        return {
            'pkg_mgr_executable_filter': self.pkg_mgr_executable_filter
        }

    def pkg_mgr_executable_filter(self, pkg_mgrs):

        return [PKG_MGRS_EXECUTABLES_MAP[pkg_mgr] for pkg_mgr in pkg_mgrs]
