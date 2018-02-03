#!/usr/bin/python

try:
    set
except NameError:
    from sets import Set as set

SUPPORTED_ROLE_PACKAGES = {
    "vagrant": "freckles-io.install-vagrant"
}


class FilterModule(object):
    def filters(self):
        return {
            'pkg_mgr_filter': self.pkg_mgr_filter
        }

    def pkg_mgr_filter(self, package_list, default_pkg_mgr, prefix=None):

        pkg_mgrs = set()

        if default_pkg_mgr and default_pkg_mgr != "auto":
            pkg_mgrs.add(default_pkg_mgr)

        for pkg in package_list:
            pkg_mgr = pkg.get("vars", {}).get("pkg_mgr", None)
            if pkg_mgr and not pkg_mgr == "auto" and not pkg_mgr == "ansible_role":
                pkg_mgrs.add(pkg_mgr)

        if prefix:
            return ["{}{}".format(prefix, item) for item in pkg_mgrs]
        else:
            return list(pkg_mgrs)
