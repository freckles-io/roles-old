Role Name
=========

A role to install and/or update 'freckles'.

As freckles usually is installed using its own bootstrap script, this role is mainly created so freckles can update itself, using it.

Role Variables
--------------

install-pkg-mgrs
======================

    use_conda: true   # otherwise use pip and sudo to install dependencies
    environment_name: "inaugurate"
    pip_base_dir: "{{ ansible_env.HOME }}/.local/inaugurate/virtualenvs/{{ environment_name }}"  # only used when 'use_conda: false'
    update: true  # whether to update freckles

Dependencies
------------

    - makkus.install-conda

Example Playbook
----------------

    - hosts: servers
      roles:
         - role: makkus.install-freckles
           update: true

License
-------

GPLv3

Author Information
------------------

Markus Binsteiner

