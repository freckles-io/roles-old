dotfiles
===========

An ansible role to manage metadata-augmented dotfiles. Pointed at a folder with such files, this role will install required applications and symbolically link (using 'stow') the dotfiles in their appropriate places.

Requirements
------------

- freckles (https://github.com/makkus/freckles)


Role Variables
-------------------

Coming soon

Dependencies
------------

    - freckles-io.install-nix
    - freckles-io.install-conda
    - elliotweiser.osx-command-line-tools
    - geerlingguy.homebrew

Example Playbook
----------------

Including an example of how to use your role (for instance, with variables passed in as parameters) is always nice for users too:

    - hosts: servers
      roles:
         - role: freckles-io.dotfiles

License
-------

GPLv3

Author Information
------------------

Markus Binsteiner
