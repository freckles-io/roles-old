import fnmatch
import json
import os
import subprocess

from ansible.module_utils.basic import *
from ansible.module_utils.basic import AnsibleModule

OTHER_PATHS_TO_CHECK = [
    os.path.expanduser("~/.local/bin"),
    os.path.expanduser("~/.local/inaugurate/conda/bin"),
    os.path.expanduser("~/.inaugurate/opt/conda/bin"),
    os.path.expanduser("~/.local/opt/conda/bin"),
    os.path.expanduser("~/.freckles/opt/conda/bin"),
    os.path.expanduser("~/miniconda3/bin"),
    os.path.expanduser("~/anaconda/bin")
]

def which(program):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        temp = []
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

        for path in OTHER_PATHS_TO_CHECK:
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None

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
        argument_spec = dict(
            conda_binary = dict(required=True),
            freckles_binary = dict(required=True)
        ),
        supports_check_mode=False
    )

    p = module.params

    executable_facts = {}

    conda_binary_path = which(p['conda_binary'])
    conda_path = os.path.abspath(os.path.join(conda_binary_path, os.pardir, os.pardir))
    if not conda_path:
        module.fail_json(msg="Could not find executable for name '{}'".format(p['conda_binary']))

    info = get_conda_info(module, conda_binary_path)
    executable_facts['conda_path'] = conda_path
    executable_facts['conda_binary_path'] = conda_binary_path
    executable_facts['conda_info'] = info

    freckles_binary_path = which(p['freckles_binary'])
    freckles_exists = bool(freckles_binary_path)

    executable_facts['freckles_binary_path'] = freckles_binary_path
    executable_facts['freckles_exists'] = freckles_exists
    #TODO freckles version?

    module.exit_json(changed=False, ansible_facts=dict(executable_facts))

if __name__ == '__main__':
    main()
