#!/usr/bin/python3
from filter_plugins import ssh_filters


def test_get_managed_keys():

    # short users variable sample
    users = [{'name': 'foo',
              'ssh_domains': ['lan', 'example.org', 'example.com']},
             {'name': 'bar',
              'ssh_domains': ['wan', 'example.org']}]

    # expected results
    r = [
        "foo.lan",
        "foo.example.org",
        "foo.example.com",
        "bar.wan",
        "bar.example.org"
    ]

    r2 = [
        "foo.lan",
        "foo.example.org",
        "foo.example.com",
        "bar.wan",
        "bar.example.org",
        "foo.example.xyz",
        "bar.example.xyz"
    ]

    assert r == ssh_filters.get_managed_keys(users, "")
    assert r2 == ssh_filters.get_managed_keys(users, "example.xyz")


def test_get_ssh_keylist():

    kpaths = [
        "/playbook_dir/private/groups/unixgroup/keys/foo.lan.pub",
        "/playbook_dir/private/groups/unixgroup/keys/foo.example.org.pub",
        "/playbook_dir/private/groups/unixgroup/keys/bar.wan.pub"
    ]

    # expected results
    r = ["foo.lan", "foo.example.org", "bar.wan"]

    assert r == ssh_filters.get_ssh_keylist(kpaths)


def test_split_keynames():

    # input
    ssh_keys = ["foo.lan",
                "foo.example.org",
                "foo.example.com",
                "bar.wan",
                "bar.example.org"]

    # expectd results
    er = [{'user': 'foo',
           'ssh_domains': ['lan', 'example.org', 'example.com']},
          {'user': 'bar',
              'ssh_domains': ['wan', 'example.org']}]
    # results
    r = ssh_filters.split_keynames(ssh_keys)

    # assert works recursively!
    assert er == r
