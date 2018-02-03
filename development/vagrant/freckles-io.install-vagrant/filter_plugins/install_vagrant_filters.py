#!/usr/bin/python

from ansible import errors

PKG_ENDING_MAP = {
    "Debian": "deb",
    "RedHat": "rpm",
    "Darwin": "dmg"
}


class FilterModule(object):
    def filters(self):
        return {
            'vagrant_binary_name_filter': self.vagrant_binary_name_filter
        }

    def vagrant_binary_name_filter(self, ansible_os_family, vagrant_version, ansible_architecture):

        try:
            return "vagrant_{}_{}.{}".format(vagrant_version, ansible_architecture, PKG_ENDING_MAP[ansible_os_family])
        except (KeyError) as e:
            raise errors.AnsibleFilterError("Platform not supported by Vagrant: {}".format(ansible_os_family))
