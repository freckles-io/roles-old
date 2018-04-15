import os

try:
    set
except NameError:
    from sets import Set as set


class FilterModule(object):
    def filters(self):
        return {
            'project_name_filter': self.project_name_filter,
            'python_dev_get_pkg_mgrs': self.python_dev_get_pkg_mgrs
        }

    def project_name_filter(self, project_path):
        return os.path.basename(project_path)

    def python_dev_get_pkg_mgrs(self, profile_vars_folders):

        raise profile_vars_folders
