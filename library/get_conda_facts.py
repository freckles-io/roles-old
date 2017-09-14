from ansible.module_utils.basic import *
from ansible.module_utils.basic import AnsibleModule

OTHER_PATHS_TO_CHECK = [
    os.path.expanduser("~/.local/inaugurate/conda/bin"),
    os.path.expanduser("~/.local/inaugurate/conda/envs/inaugurate/bin"),
    os.path.expanduser("~/.local/inaugurate/virtualenvs/inaugurate/bin"),
    os.path.expanduser("~/.local/bin"),
    os.path.expanduser("~/miniconda3/bin"),
    os.path.expanduser("~/anaconda/bin")
]


# we assume that if freckles is installed with conda, the path to the binary has the token 'conda' in it
def which(program, install_method):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    paths = []
    if fpath:
        if is_exe(program):
            program = os.path.realpath(program)
            if 'conda' in program:
                if install_method == 'conda' or install_method == 'auto':
                    return (program, 'conda')
            else:
                if install_method == 'pip' or install_method == 'auto':
                    return (program, 'pip')
    else:
        temp = []
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                exe_file = os.path.realpath(exe_file)
                if 'conda' in exe_file:
                    if install_method == 'conda' or install_method == 'auto':
                        return (exe_file, 'conda')
                else:
                    if install_method == 'pip' or install_method == 'auto':
                        return (exe_file, 'pip')

        for path in OTHER_PATHS_TO_CHECK:
            paths.append(path)
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                exe_file = os.path.realpath(exe_file)
                if 'conda' in exe_file:
                    if install_method == 'conda' or install_method == 'auto':
                        return (exe_file, 'conda')
                else:
                    if install_method == 'pip' or install_method == 'auto':
                        return (exe_file, 'pip')

    return (None, 'auto')


def get_conda_info(module, conda_path):
    cmd = "{} env list --json".format(conda_path)
    rc, stdout, stderr = module.run_command(cmd)

    if rc != 0:
        return module.fail_json(msg="Can't list conda envs".format(stderr))
    pass

    info = json.loads(stdout)

    return info


def main():
    module = AnsibleModule(
        argument_spec=dict(
            conda_binary=dict(required=True),
            freckles_binary=dict(required=True),
            install_method=dict(required=False, default="auto")
        ),
        supports_check_mode=False
    )

    p = module.params

    install_method = p['install_method']

    executable_facts = {}

    conda_binary_path, not_important = which(p['conda_binary'], install_method)
    freckles_binary_path, i_method = which(p['freckles_binary'], install_method)
    freckles_exists = bool(freckles_binary_path)
    if freckles_exists:
        freckles_parent_path = os.path.abspath(os.path.join(freckles_binary_path, os.pardir))

    if not conda_binary_path and not freckles_binary_path:
        executable_facts['freckles_binary_path'] = False
        executable_facts['conda_binary_path'] = False
        executable_facts['existing_install_method'] = None
        executable_facts['freckles_exists'] = False
        executable_facts['conda_exists'] = False
        module.exit_json(changed=False, ansible_facts=dict(executable_facts))

    if not conda_binary_path and freckles_binary_path:
        executable_facts['freckles_binary_path'] = freckles_binary_path
        executable_facts['freckles_parent_path'] = freckles_parent_path
        executable_facts['freckles_exists'] = True
        executable_facts['conda_exists'] = False
        executable_facts['existing_install_method'] = i_method
        module.exit_json(changed=False, ansible_facts=dict(executable_facts))

    conda_path = os.path.abspath(os.path.join(conda_binary_path, os.pardir, os.pardir))

    info = get_conda_info(module, conda_binary_path)

    if conda_binary_path and not freckles_binary_path:
        executable_facts['conda_path'] = conda_path
        executable_facts['existing_install_method'] = None
        executable_facts['conda_binary_path'] = conda_binary_path
        executable_facts['freckles_exists'] = False
        executable_facts['conda_info'] = info
        executable_facts['conda_info'] = info
        module.exit_json(changed=False, ansible_facts=dict(executable_facts))

    if conda_binary_path and freckles_binary_path:
        executable_facts['conda_path'] = conda_path
        executable_facts['existing_install_method'] = i_method
        executable_facts['conda_binary_path'] = conda_binary_path
        executable_facts['conda_info'] = info
        executable_facts['freckles_binary_path'] = freckles_binary_path
        executable_facts['freckles_parent_path'] = freckles_parent_path
        executable_facts['freckles_exists'] = True
        module.exit_json(changed=False, ansible_facts=dict(executable_facts))
        # TODO freckles version?


if __name__ == '__main__':
    main()
