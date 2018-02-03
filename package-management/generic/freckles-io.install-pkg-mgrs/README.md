install-pkg-mgrs
======================

An convenience ansible role to install (supported) package managers.

Currently supported:

 - conda
 - nix
 - homebrew (will only be installed on Mac OS X, otherwise ignored)

Role Variables
-------------------

    pkg_mgrs:
      - nix
      - conda

Dependencies
----------------

     - makkus.install-nix
     - makkus.install-conda
     - elliotweiser.osx-command-line-tools
     - geerlingguy.homebrew


Example Playbook
----------------

    - hosts: servers
      roles:
         - role: makkus.install-pkg-mgrs
           pkg_mgrs:
             - nix
             - conda

License
-------

GPLv3

Author Information
------------------

Markus Binsteiner
