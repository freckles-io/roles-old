box-basics
==============

Convenience role to gather common tasks that need to be done to prepare a role for 'proper' role execution.

Currently, this updates the apt cache (twice, if the first time fails -- this is a weird issue for some vanilla virtualboxes), and installs package managers and git (using a custom package manager if specified).

Role Variables
--------------

None

Dependencies
------------

    - makkus.install-pkg-mgrs

Example Playbook
----------------

    - hosts: servers
      roles:
         - makkus.box-basics

License
-------

GPLv3

Author Information
------------------

Markus Binsteiner
