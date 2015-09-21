accounts
========

An ansible role to create and configure accounts on a host.

role summary:
  1. create groups
  2. create users and and create a ssh key pair for each of them (all of this using the user module)
  3. Install a public ssh key to authorized_keys to remotely manage the machine
  4. Copy the public key to the control machine
  5. Template the ~/.ssh/config in order to be able to use the keys
  6. Template a simple bash script to clone dotfiles repos after a user has
    manually install his public key in the ssh repo.

Role Variables
--------------

Defaults:

```yaml
user_ssh_config_defaults:
  ForwardX11Trusted: yes
  ControlPersist: 2m
  ControlMaster: auto
  ControlPath: '~/.ssh/controlmasters/%r@%h:%p'

# directory containing sensitive data
private_dir: "{{ playbook_dir }}/private"

users: []
req_groups: []
users_removed: []
groups_removed: []
```

To add users, you must load them from a vars_files:

```yaml
users:
  - name: "foo"
    groups: 'adm,wheel,lp,users'
    authorized:           # Keys to add to authorized_keys
      - "ssh-1"
      - "ssh-2"
    append: "no"        # (Optional) yes by default
    pass: "$6$...."     # (Optional) Set the user's password to this crypted value.
    comment: "bla"      # (Optional) User Full name
    shell: "/bin/bash"  # (Optional) Set the user's shell. defaults to /bin/bash
    home: "/home/foo"   # (Optional) default to /home/<username>
    system: no          # (Optional)
    move_home: no       # (Optional)
    non_unique: no      # (Optional)
    update_password: no # (Optional) default to on_create (will change passwd if they differ
```

To create groups:

```yaml
groups:
  - name: "foo"
    gid: 2000           # (Optional)
    system: no          # (Optional)
  - name: "bar"
    gid: 4000
    system: no
```

Dependencies
------------

None.

Example Playbook
----------------

```yaml
- hosts: servers

  vars_files:
    - "{{ playbook_dir }}/{{ private_dir }}/users/users.yml"

  roles:
    - { role: archf.accounts }
```

License
-------

MIT

Author Information
------------------

Felix Archambault
