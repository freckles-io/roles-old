python-dev
=========

An ansible role to install potential dependencies of a python project, create a virtualenv, and install the project into that virtualenv, ready for development work.

**NOTE**: currently there is a problem with python 3 and Mac OS X. Also, I'm not sure whether the default 'freckle' virtualenv doesn't interfere with this role, so sometimes the wrong python binary is used. In short: this needs more work.

Requirements
------------

- TBC

Role Variables
--------------

Coming soon.

Dependencies
------------

TBC

Example Playbook
----------------

    - hosts: servers
      roles:
         - role: makkus.python-dev

License
-------

GPLv3

Author Information
------------------

Markus Binsteiner
