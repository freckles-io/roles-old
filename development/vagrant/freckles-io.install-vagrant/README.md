install-vagrant
====================

Downloads the appropriate Vagrant package, installs it.

Note: for now download happens with the get_url module, setting 'validate_certs' to 'false', because of this issue with Ansible 2.3: https://github.com/ansible/ansible/pull/26235


Role Variables
--------------

    # whether to download and install Vagrant, even if it already exists
    force_update: no
    # the vagrant version to install
    vagrant_version: 1.9.7
    # the download url
    vagrant_download_url: https://releases.hashicorp.com/vagrant
    # where to download the package (useful if you want to cache the download)
    vagrant_download_path: "/tmp/_vagrant_download"
    # whether to delete the downloaded package afterwards
    delete_download_after: yes


Dependencies
------------

curl (on Mac OS X) -- get_url errors out for some reason, at least on El Capitan

Example Playbook
----------------

    - hosts: localhost
      roles:
         - makkus.install-vagrant

License
-------

GPL v3

Author Information
------------------

Markus Binsteiner
