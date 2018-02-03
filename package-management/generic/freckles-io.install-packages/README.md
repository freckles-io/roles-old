install-packages
======================

An ansible role to install a list of packages, installing required package managers if necessary.

Role Variables
--------------

    package_install_list: 
      - vars:
          name: zile
          pkg_mgr: auto'
      - vars:
          name: emacs
          pkg_mgr: nix

Dependencies
------------

    - makkus.install-pkg-mgrs
    - makkus.install-conda
    - makkus.install-nix
    - makkus.install-vagrant

Example Playbook
----------------

    - hosts: localhost
      roles:
         - makkus.freckles
           package_listall_list:
             - vars:
                 name: zile
             - vars:
                 name: emacs
                 pkg_mgr: nix
             - vars:
                 name: nano
                 pkg_mgr: conda
             - vars:
                 name: vagrant
                 pkg_mgr: ansible_role

License
-------

GPLv3

Author Information
------------------

Markus Binsteiner
