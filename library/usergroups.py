#!/usr/bin/python
# -*- coding: utf-8 -*-

import grp
from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(
            system=dict(default="False", type='bool'),
        ),
        supports_check_mode=True,
    )

    params = module.params

    # grouplist = []

    # # get system groups
    # if params['system']:
    #     for g in grp.getgrall():
    #         if g[2] < 1000:
    #             grouplist.append({'name': g[0],
    #                               'gid': g[2],
    #                               'users': g[3]})

    # # get normal groups
    # else:
    #     for g in grp.getgrall():
    #         if g[2] > 999:
    #             grouplist.append({'name': g[0],
    #                               'gid': g[2],
    #                               'users': g[3]})

    groupdict = {}

    # get system groups
    if params['system']:
        for g in grp.getgrall():
            if g[2] < 1000:
                groupdict[g[0]]={'gid': g[2], 'users': g[3]}

    # get normal groups
    else:
        for g in grp.getgrall():
            if g[2] > 999:
                groupdict[g[0]] = {'gid': g[2], 'users': g[3]}

    module.exit_json(ansible_facts={'ansible_usergroups': groupdict})
    # module.exit_json(ansible_facts={'ansible_usergroups': grouplist})

if __name__ == '__main__':
    main()
