#!/usr/bin/python

import copy
import re
from collections import OrderedDict
import os
import yaml
from ansible import errors
from frkl import frkl
from nsbl.nsbl import ensure_git_repo_format
from six import string_types
from freckles.freckles_defaults import DEFAULT_PROFILE_VAR_FORMAT, DEFAULT_VAR_FORMAT, DEFAULT_PACKAGE_FORMAT
from freckles.utils import render_dict

try:
    set
except NameError:
    from sets import Set as set

METADATA_CONTENT_KEY = "freckle_metadata_file_content"
DEFAULT_FRECKLES_PROFILE_NAME = "__freckles_default__"

SUPPORTED_ROLE_PACKAGES = {
    "vagrant": "freckles-io.install-vagrant"
}

# DEFAULT_PROFILE_VAR_FORMAT = {"child_marker": "profiles",
#                               "default_leaf": "profile",
#                               "default_leaf_key": "name",
#                               "key_move_map": {'*': "vars"}}

# DEFAULT_VAR_FORMAT = {"child_marker": "childs",
#                       "default_leaf": "vars",
#                       "default_leaf_key": "name",
#                       "key_move_map": {'*': "vars"}}

# DEFAULT_PACKAGE_FORMAT = {"child_marker": "packages",
#                           "default_leaf": "vars",
#                           "default_leaf_key": "name",
#                           "key_move_map": {'*': "vars"}}


class FilterModule(object):
    def filters(self):
        return {
            'read_profile_vars_filter': self.read_profile_vars_filter,
            'git_repo_filter': self.git_repo_filter,
            'create_package_list_filter': self.create_package_list_filter,
            'create_package_list_from_var_filter': self.create_package_list_from_var_filter,
            'create_result_list_filter': self.create_result_list_filter,
            'extra_pkg_mgrs_filter': self.extra_pkg_mgrs_filter,
            'flatten_profiles_filter': self.flatten_profiles_filter,
            'flatten_vars_filter': self.flatten_vars_filter,
            'folder_vars_filter': self.folder_vars_filter,
            'file_list_filter': self.file_list_filter,
            'relative_path_filter': self.relative_path_filter,
            'first_valid_default_list_filter': self.first_valid_default_list_filter,
            'calculate_local_freckle_folder': self.calculate_local_freckle_folder,
            'user_input_merge_filter': self.user_input_merge_filter,
            'global_vars_filter': self.global_vars_filter,
            'sort_profiles_filter': self.sort_profiles_filter
            # 'get_used_profile_names': self.get_used_profile_names,
            # 'create_profile_metadata': self.create_profile_metadata
        }

    def sort_profiles_filter(self, profile_list, profile_order):

        result = []

        for p in profile_order:
            for pp in profile_list:
                if pp[0] == p:
                    result.append(pp)

        return result


    def global_vars_filter(self, global_folder_vars):

        result = {}

        for path, folder_vars in global_folder_vars.items():

            frkl.dict_merge(result, folder_vars, copy_dct=False)

        return result

    def user_input_merge_filter(self, freckles_metadata, user_vars):

        result = {}
        profiles_already_done = set()

        # pre-process user_vars
        user_vars_folder_endings = {}
        user_vars_default = {}
        for key, v in user_vars.items():
            if ':' not in key:
                user_vars_default[key] = v
            else:
                path_ending, profile = key.rsplit(':', 1)
                user_vars_folder_endings.setdefault(profile, {}).setdefault(path_ending, []).append(v)

        for path, folder_metadata in freckles_metadata.items():

            new_vars_list = []
            # profiles_to_use = folder_metadata["folder_metadata"]["profiles_to_use"]
            vars_list = folder_metadata["vars"]

            for vars_item in vars_list:
                profile_md = vars_item["profile"]
                profile_name = profile_md["name"]
                # if profile_name == "freckle":
                    # continue

                new_v = copy.deepcopy(vars_item.get("vars", {}))
                for profile, profile_vars in user_vars_default.items():

                    if profile == profile_name:
                        frkl.dict_merge(new_v, profile_vars, copy_dct=False)
                        profiles_already_done.add(profile)

                for profile, folder_endings_dict in user_vars_folder_endings.items():

                    if profile == profile_name:
                        for ending, profile_vars_list in folder_endings_dict.items():
                            if path.endswith(ending):
                                for profile_vars in profile_vars_list:
                                    frkl.dict_merge(new_v, profile_vars, copy_dct=False)
                                    profiles_already_done.add(profile)

                new_vars_list.append({"profile": profile_md, "vars": new_v})

            # if there are no folder vars to merge, we just use the user input directly
            for profile, profile_vars in user_vars_default.items():
                if profile not in profiles_already_done:
                    new_vars_list.append({"profile": {"name": profile}, "vars": profile_vars})

            for profile, folder_endings_dict in user_vars_folder_endings.items():

                if profile not in profiles_already_done:
                    for ending, profile_vars_list in folder_endings_dict.items():
                        if path.endswith(ending):
                            for profile_vars in profile_vars_list:
                                frkl.dict_merge(new_v, profile_vars, copy_dct=False)


            folder_metadata["vars"] = new_vars_list

        # replace variable strings
        for folder, all_vars in freckles_metadata.items():
            replacement_dict = {
                "freckle_path": folder
            }
            freckles_metadata[folder] = render_dict(all_vars, replacement_dict)

        return freckles_metadata


    def calculate_local_freckle_folder(self, path, user_home):

        if path.startswith("~"):
            result = os.path.join(user_home, path[2:])
        elif path.startswith("/"):
            result = path
        else:
            result = os.path.join(user_home, path)

        return result

    def first_valid_default_list_filter(self, default_item, *other_defaults):

        if default_item:
            return default_item

        for item in other_defaults:
            if item:
                return item

        # return last element
        return item

    def relative_path_filter(self, list_of_files, path):

        return [os.path.relpath(f, path) for f in list_of_files]

    def file_list_filter(self, list_of_files, filter_regex):

        r = re.compile(filter_regex)
        result = filter(r.match, list_of_files)
        return result

    def folder_vars_filter(self, freckles_profile_folders, freckles_metadata, ansible_env):
        """Merge all vars of all profiles per folder.
        """

        result = {}
        for folder, metadata in freckles_profile_folders.items():
            temp_dict = {}
            freckle_vars = freckles_metadata[folder]["vars"]
            for v_item in freckle_vars:
                frkl.dict_merge(temp_dict, v_item, copy_dct=False)

            folder_vars = metadata.get("vars", [])
            for fv in folder_vars:
                frkl.dict_merge(temp_dict, fv, copy_dct=False)

            if "change_owner" not in temp_dict.get("vars", {}).keys():
                temp_dict.get("vars", {})["change_owner"] = "owner" in temp_dict.get("vars", {}).keys()

            default_user = ansible_env.get("USER", "root")
            default_home = ansible_env.get("HOME", "/root")
            defaults_dict = { "vars": {
                "owner": default_user,
                 #"freckle_group": default_group,
                "stow_root": default_home,
                "staging_method": False,
                "staging_force": False,
                }
            }

            frkl.dict_merge(defaults_dict, temp_dict, copy_dct=False)

            result[folder] = defaults_dict.get("vars", {})

        return result

    def flatten_vars_filter(self, freckles_vars):

        if not freckles_vars:
            return {}

        chain = [frkl.FrklProcessor(DEFAULT_VAR_FORMAT)]
        try:
            frkl_obj = frkl.Frkl(freckles_vars, chain)
            # mdrc_init = {"append_keys": "vars/packages"}
            # frkl_callback = frkl.MergeDictResultCallback(mdrc_init)
            frkl_callback = frkl.MergeResultCallback()
            vars_new = frkl_obj.process(frkl_callback)
            return vars_new[0]["vars"]

        except (frkl.FrklConfigException) as e:
            raise errors.AnsibleFilterError(
                "Can't read freckle metadata file '{}/.freckle': {}".format(freckle_folder, e.message))

    def flatten_profiles_filter(self, freckles_metadata):
        """This function re-arranges a list of freckle folders.

        Input is a list of folders, output is a dict of folder-profile/folders.
        """

        temp = {}
        profiles_available = set()
        profile_items = []

        for folder, all_vars in freckles_metadata.items():

            folder_metadata = all_vars["folder_metadata"]
            temp_profiles_to_use = ['freckle']
            temp_profiles_to_use.extend(folder_metadata["profiles_to_use"])
            files = folder_metadata["files"]
            extra_vars = all_vars.get("extra_vars", {})

            if "__auto__" in temp_profiles_to_use:
                auto_profiles = []
                vars_temp = all_vars["vars"]
                for v in vars_temp:
                    tp = v["profile"]["name"]
                    if tp not in auto_profiles:
                        auto_profiles.append(tp)
                new_profiles = []

                for p in temp_profiles_to_use:
                    if p == "__auto__":
                        new_profiles.extend(auto_profiles)
                    else:
                        new_profiles.append(p)

                temp_profiles_to_use = new_profiles

            for profile_name in temp_profiles_to_use:

                temp.setdefault(profile_name, {}).setdefault(folder, {})
                temp[profile_name][folder]["extra_vars"] = extra_vars
                temp[profile_name][folder]["files"] = files

                if profile_name not in profile_items:
                    profile_items.append(profile_name)

            for metadata in all_vars["vars"]:
                profile_md = metadata.pop("profile")
                profile = profile_md["name"]
                profiles_available.add(profile)

                temp.setdefault(profile, {}).setdefault(folder, {}).setdefault("vars", []).append(metadata)


        profiles_available = list(profiles_available)

        # profiles_to_run = OrderedDict()
        profiles_to_run = []
        debug_freckle = False

        # TODO: simplify, can probably use profile_items list
        for profile, folder_vars in temp.items():
            if debug_freckle:
                break
            for folder, f_vars in folder_vars.items():
                profiles_to_use_temp = freckles_metadata[folder]["folder_metadata"]["profiles_to_use"]
                if "debug-freckle" in profiles_to_use_temp:
                    debug_freckle = True
                    break

        if debug_freckle:
            #profiles_to_run["debug-freckle"] = {}
            temp_vars = {}
            profiles_to_use = ["debug-freckle"]

            for profile, folder_vars in temp.items():
                for folder, f_vars in folder_vars.items():
                    files = freckles_metadata[folder]["folder_metadata"]["files"]
                    temp_vars.setdefault(folder, {}).setdefault("vars", []).extend(
                        f_vars.get("vars", []))
                    temp_vars[folder]["extra_vars"] = f_vars.get("extra_vars", {})
                    temp_vars[folder]["files"] = files
            profiles_to_run.append(("debug-freckle", temp_vars))

        else:

            for profile in profile_items:
            # for profile, folder_vars in temp.items():
                folder_vars = temp[profile]
                temp_folder_vars = {}

                for folder, f_vars in folder_vars.items():


                    temp_folder_vars.setdefault(folder, {}).setdefault("vars", [])

                    temp_folder_vars[folder]["extra_vars"] = f_vars["extra_vars"]
                    temp_folder_vars[folder]["files"] = f_vars["files"]

                    if folder in temp.get('freckle', {}).keys():

                        for f_var_item in temp['freckle'][folder].get("vars", []):
                            t = f_var_item.get("vars", None)
                            if t:
                                temp_folder_vars[folder]["vars"].append({"vars": t})

                    vars = f_vars.get("vars", [])
                    temp_folder_vars[folder]["vars"] = vars

                profiles_to_run.append((profile, temp_folder_vars))


        # add some stats to be used by the profile dispatcher if necessary
        profiles_total = len(profiles_to_run)
        profile_index = 0
        for p in profiles_to_run:
            profile_name = p[0]
            folders = p[1]
            folders_total = len(folders)
            folder_index = 0
            for folder, folder_metadata in folders.items():
                stats = {}
                stats["profiles"] = {"total": profiles_total, "current": profile_index}
                stats["folders"] = {"total": folders_total, "current": folder_index}
                folder_metadata["stats"] = stats
                folder_index = folder_index + 1
            profile_index = profile_index + 1

        return profiles_to_run

    # def get_used_profile_names(self, freckles_metadata):

    #     profile_names = set()

    #     for folder, profiles in freckles_metadata.items():

    #         profile_names.update(profiles.keys())

    #     profile_names.discard(DEFAULT_FRECKLES_PROFILE_NAME)

    #     return list(profile_names)

    def read_profile_vars_filter(self, folders_metadata):

        temp_vars = {}
        extra_vars = {}

        for folder, metadata in folders_metadata.items():

            raw_metadata = metadata.pop(METADATA_CONTENT_KEY, False)
            if raw_metadata:
                md = yaml.safe_load(raw_metadata)
                if not md:
                    md = []
                    # if isinstance(md, (list, tuple)):
                    # md = {"vars": md}
            else:
                md = [{"profile": {"name": "freckle"}, "vars": {}}]

            temp_vars.setdefault(folder, []).append(md)

            extra_vars_raw = metadata.pop("extra_vars", False)
            if extra_vars_raw:
                for rel_path, extra_metadata_raw in extra_vars_raw.items():
                    extra_metadata = yaml.safe_load(extra_metadata_raw)
                    if not extra_metadata:
                        # this means there was an empty file. We interprete that as setting a flag to true
                        extra_metadata = True

                    sub_path, filename = os.path.split(rel_path)
                    extra_vars.setdefault(folder, {}).setdefault(sub_path, {})[filename[1:-8]] = extra_metadata

        result = {}
        for freckle_folder, metadata_list in temp_vars.items():

            chain = [frkl.FrklProcessor(DEFAULT_PROFILE_VAR_FORMAT)]
            try:
                frkl_obj = frkl.Frkl(metadata_list, chain)
                # mdrc_init = {"append_keys": "vars/packages"}
                # frkl_callback = frkl.MergeDictResultCallback(mdrc_init)
                frkl_callback = frkl.MergeResultCallback()
                profile_vars_new = frkl_obj.process(frkl_callback)
                result.setdefault(freckle_folder, {})["vars"] = profile_vars_new
                result[freckle_folder]["extra_vars"] = extra_vars.get(freckle_folder, {})
                result[freckle_folder]["folder_metadata"] = folders_metadata[freckle_folder]
            except (frkl.FrklConfigException) as e:
                raise errors.AnsibleFilterError(
                    "Can't read freckle metadata file '{}/.freckle': {}".format(freckle_folder, e.message))
        return result

    def create_package_list_from_var_filter(self, parent_vars_list, packages_key):

        if isinstance(parent_vars_list, dict):
            parent_vars_list = [parent_vars_list]

        result = []
        for parent_vars in parent_vars_list:
            parent_vars_copy = copy.deepcopy(parent_vars.get("vars", {}))
            package_list = parent_vars_copy.pop(packages_key, [])
            pkg_config = {"vars": parent_vars_copy, "packages": package_list}

            chain = [frkl.FrklProcessor(DEFAULT_PACKAGE_FORMAT)]
            frkl_obj = frkl.Frkl(pkg_config, chain)
            pkgs = frkl_obj.process()
            result.extend(pkgs)

        return sorted(result, key=lambda k: k.get("vars", {}).get("name", "zzz"))

    def extra_pkg_mgrs_filter(self, freckles_profile_metadata):

        extra_pkg_mgrs = set()

        for folder, folder_metadata in freckles_profile_metadata.items():

            var_list = folder_metadata.get("vars", [])
            for metadata in var_list:
                extras = metadata.get("vars", {}).get("pkg_mgrs", [])
                extra_pkg_mgrs.update(extras)

        return list(extra_pkg_mgrs)

    def create_package_list_filter(self, freckles_profile_metadata):
        """
        Tries to get all packages from all freckle items.
        """

        result = []

        for folder, folder_metadata in freckles_profile_metadata.items():

            var_list = folder_metadata.get("vars", [])
            for metadata in var_list:
                parent_vars = copy.deepcopy(metadata.get("vars", {}))
                parent_vars.pop("packages", None)

                packages = metadata.get("vars", {}).get("packages", [])

                pkg_config = {"vars": parent_vars, "packages": packages}

                chain = [frkl.FrklProcessor(DEFAULT_PACKAGE_FORMAT)]
                frkl_obj = frkl.Frkl(pkg_config, chain)
                pkgs = frkl_obj.process()

                result = result + pkgs

        #return sorted(result, key=lambda k: k.get("vars", {}).get("name", "zzz"))
        return result

    def create_result_list_filter(self, freckles_profile_metadata, var_to_extract, pkg_format):

        result = []

        for folder, folder_metadata in freckles_profile_metadata.items():

            var_list = folder_metadata.get("vars", [])
            for metadata in var_list:
                parent_vars = copy.deepcopy(metadata.get("vars", {}))
                parent_vars.pop(var_to_extract, None)

                packages = metadata.get("vars", {}).get(var_to_extract, [])

                pkg_config = {"vars": parent_vars, var_to_extract: packages}

                chain = [frkl.FrklProcessor(pkg_format)]
                frkl_obj = frkl.Frkl(pkg_config, chain)
                pkgs = frkl_obj.process()

                result = result + pkgs

        return sorted(result, key=lambda k: k.get("vars", {}).get("name", "zzz"))

    def git_repo_filter(self, freckles):

        if isinstance(freckles, (string_types, dict)):
            freckles = [freckles]
        elif not isinstance(freckles, (list, tuple)):
            raise Exception(
                "Not a valid type for dotfile_repo, can only be dict, string, or a list of one of those: {}".format(
                    freckles))

        result = []
        # TODO: check valid
        for fr in freckles:
            if "url" not in fr.keys() or not fr["url"]:
                temp = {"repo": None, "dest": fr["path"]}
            else:
                temp = ensure_git_repo_format(fr["url"], dest=fr.get("path", None))
            result.append(temp)

        return result
