# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)

from os import path
from ansible.errors import AnsibleFilterError


__metaclass__ = type


def split_keynames(knames):
    """
    Get a list of key owner and domain from kpath basename.

    Arg must be a list.

    Example of expected input:

        input = ["foo.lan",
                "foo.example.org",
                "foo.example.com",
                "bar.wan",
                "bar.example.org"]

    And it should output:

        output = [{'name': 'foo',
                'ssh_domains': ['lan', 'example.org', 'example.com']},
                {'name': 'bar',
                'ssh_domains': ['wan', 'example.org']}]
    """

    if not isinstance(knames, list):
        raise AnsibleFilterError("| expects lists, got " + repr(knames))

    r = []

    for kname in knames:
        try:
            v = kname.split(".", 1)
        except:
            raise AnsibleFilterError("keyname should follow a dotted notation \
                            like '<owner>.<domain.tld>' got instead: " + kname)

        nbusers = len(r)
        found = False

        if nbusers:
            # loop over output list
            for i in range(nbusers):
                # see if user is already there
                if r[i].get("user") == v[0]:

                    r[i]["ssh_domains"].append(v[1])
                    found = True

                # append to list
                else:
                    found = False

        if not found:
                r.append({"user": v[0], "ssh_domains": [v[1]]})

    return r


def get_managed_keys(users, default_domain):
    """
    Get a list of all managed keys.

    Managed keys are those defined in users.yml inside the 'users' variable.
    Return a list of basename in the form <owner>.<domain>.
    """

    if not isinstance(users, list):
        raise AnsibleFilterError("| expects lists, got " + repr(users))

    r = []

    for user in users:
        for domain in user["ssh_domains"]:
            r.append(user["name"] + "." + domain)

    # second append the default domain if defined
    if default_domain:
        for user in users:
            r.append(user["name"] + '.' + default_domain)

    return r


def get_ssh_keylist(kpaths):
    """
    Get a list of ssh keys from absolute paths.


    kpaths is a generator returned by another jinja2 filter.

    Here is the input arg before path is filtered with the jinja2 map filter
    and only paths are fed to this function.

    "ssh_keys": {
        "files": [
            {
                [...snip...]
                "path": "/[...]/playbook_dir/private/groups/unixgroup/keys/foo.lan.pub",
                [...snip...]
            },
            {
                [...snip...]
                "path": "/[...]/playbook_dir/private/groups/unixgroup/keys/bar.github.com.pub",
                [...snip...]
            }
            ]
    }

    Returned expired keys have no '.pub' extension.
    """

    r = []

    for kpath in kpaths:
        r.append(path.splitext(path.basename(kpath))[0])

    return r


class FilterModule(object):
    ''' Ansible ssh jinja2 filters '''

    def filters(self):
        return {'get_managed_keys': get_managed_keys,
                'get_ssh_keylist': get_ssh_keylist,
                'split_keynames': split_keynames, }
