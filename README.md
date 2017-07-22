install-conda
==================

Ansible role to install the conda package manager.

Currently it is only possible to install miniconda, not 'full-blown' anaconda.

Requirements
------------

Developed this role with Ansible 2.3, not sure if earlier versions will work.

Role Variables
--------------

The variables this role supports are:

    conda_rel_path: ".local/opt"   # path where to install (mini)conda (relative to base path)
    conda_parent_dir: "{{ ansible_env.HOME }}/{{ conda_rel_path }}"   # full path to where to install (mini)conda
    add_to_path: true   # whether to add nix to the path in rc files
    # rc files to add nix path loading line to
    rc_files_to_add_path_to:
      - "{{ ansible_env.HOME }}/.profile"

Dependencies
------------

No dependencies.

Example Playbook
----------------

    - hosts: localhost
      roles:
         - makkus.install-conda

License
-------

GPL v3

Author Information
------------------

Markus Binsteiner
