#!/usr/bin/env python
from ansible.plugins.action import ActionBase
from ansible.errors import AnsibleError
from ansible.utils.vars import isidentifier

import dpath

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        suffix_to_merge = self._task.args.get('suffix_to_merge', '')
        merged_var_name = self._task.args.get('merged_var_name', '')
        additional_merge_tree = self._task.args.get('additional_merge_tree', {})

        all_keys = task_vars.keys()

        if not merged_var_name:
            raise AnsibleError("merged_var_name must be set")
        if not isidentifier(merged_var_name):
            raise AnsibleError("merged_var_name '%s' is not a valid identifier" % merged_var_name)

        keys = sorted([key for key in task_vars.keys()
                if key.endswith(suffix_to_merge)])

        display.v("Merging vars in this order: {}".format(keys))

        merge_vals = [self._templar.template(task_vars[key]) for key in keys]

        merged = {}
        for val in merge_vals:
            dpath.util.merge(dst=merged, src=val, flags=dpath.util.MERGE_ADDITIVE)

        for k in additional_merge_tree:
            try:
                r = dpath.util.get(merged, k)
                m = {}
                if isinstance(r, list):
                    for d in r:
                        if isinstance(d, dict):
                            display.v("Merging values {} in path {}".format(d, k))
                            dpath.util.merge(dst=m, src=d, flags=dpath.util.MERGE_ADDITIVE)

                    if m:
                        display.v("Set merged values {} to path {}".format(m, k))
                        dpath.util.set(merged, k, [m])
                else:
                    display.warning("Merge not implemented for followin type {} by path".format(type(r), k))
            except KeyError as e:
                display.warning("Key doesnt exists: {}".format(e))

        return {
            'ansible_facts': {merged_var_name: merged},
            'ansible_facts_cacheable': False,
            'changed': False,
        }
