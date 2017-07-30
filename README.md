freckles
===========

An ansible role to manage dotfiles and working environment setups in general

Requirements
-----------------

- frkl python package

Role Variables
-------------------

    freckles_profiles: []  # list of profiles to use, defaults to use all profiles that can be found
    freckles_repos: [] # list of repos to checkout
    freckles_stow: False   # whether to stow child folders within profiles or the root repository (if no profile folders are found and no profiles are specified in the 'freckles_profiles' variable)
    freckles_stow_target_dir: "{{ ansible_env.HOME }}"   # default stow target directory


Dependencies
------------

    - makkus.install-nix
    - makkus.install-conda
    - elliotweiser.osx-command-line-tools
    - geerlingguy.homebrew

Example Playbook
----------------

    - hosts: servers
      roles:
         - role: makkus.freckles

License
-------

GPLv3

Author Information
------------------

Markus Binsteiner
