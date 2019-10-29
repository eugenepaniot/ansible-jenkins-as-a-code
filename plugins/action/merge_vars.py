#!/usr/bin/env python
from ansible.plugins.action import ActionBase
from ansible.errors import AnsibleError
from ansible.utils.vars import isidentifier
import itertools

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
        expected_type = self._task.args.get('expected_type', 'dict')
        additional_merge_tree = self._task.args.get('additional_merge_tree', [])
        additional_merge_by_key = self._task.args.get('additional_merge_by_key', [])

        all_keys = task_vars.keys()

        if not merged_var_name:
            raise AnsibleError("merged_var_name must be set")
        if not isidentifier(merged_var_name):
            raise AnsibleError("merged_var_name '%s' is not a valid identifier" % merged_var_name)

        keys = sorted([key for key in task_vars.keys()
                if key.endswith(suffix_to_merge)])

        display.v("Merging vars in this order: {}".format(keys))

        merge_vals = [self._templar.template(task_vars[key]) for key in keys]

        merged = None
        if expected_type == 'list':
            merged = list(itertools.chain.from_iterable(merge_vals))
        else:
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

        for k in additional_merge_by_key:
            try:
                key, merge_by = list(k.items())[0]

                def keyfunc(x):
                    return x[merge_by]

                m = []
                data = sorted(dpath.util.get(merged, key), key=keyfunc)
                for merge_value, group in itertools.groupby(data, keyfunc):
                    mm = {}
                    display.v("Merging path {} by key {} and value {}".format(key, merge_by, merge_value))
                    for g in list(group):
                        dpath.util.merge(dst=mm, src=g, flags=dpath.util.MERGE_ADDITIVE)

                    m.append(mm)

                if m:
                    dpath.util.new(merged, key, m)

            except KeyError as e:
                display.warning("Key {} doesnt exists: in {}".format(e, k))

        return {
            'ansible_facts': {merged_var_name: merged},
            'ansible_facts_cacheable': False,
            'changed': False,
        }
