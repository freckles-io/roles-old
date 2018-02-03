import os

try:
    set
except NameError:
    from sets import Set as set


class FilterModule(object):
    def filters(self):
        return {
            'project_name_filter': self.project_name_filter
        }

    def project_name_filter(self, project_path):
        return os.path.basename(project_path)
