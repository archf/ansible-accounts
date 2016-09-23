# ansible-accounts

A role to create and configure user accounts and groups on a host.

## Description


### Usergroups

This role works in a usergroups paradigm. As your coworkers also needs to
login on the same servers, user accounts are configured by adding one or
multiple usergroups composed of one or more individual users that will end up
attached to the unix group named after the usergroup name. Phew!

### Workstations

You will often see around the term `workstations` either in the code or in
part of variable's name or as an ansible group name. Workstations can be seen
as the main working machine. For instance a laptop or a desktop used for
daily work by a single person should be part of this host group.

So what does it change?

For hosts in this special host group, the role behavior will change as not
all `usergroups` nor every user of these usergroups are configured on the
target. In fact, the sole user that will be added is the one which has a
matching `workstation: <hostname>` configured in his user profile.

### SSH keys management

Private ssh keys are **only managed on workstations**. Agent-fowarding should be
considered when using a `jumphost` or hopping through a bastion host. To make
things manageable and flexible, following logic is used to allow a user to
have have multiple ssh keys.

  * default keyname id_rsa and id_rsa.pub are not use for complexity reasons
  * default keys give access to an internal domain (i.e. company domain)
  * other keys might optionaly exist and give access to other external domains
  * keynames follow a `<user>.<domain>`

The `domain` part is important as it hints you what it gives access to. As
such, this is the role behavior regarding your keyring management.

  * default keys are deployed as <user>.<domain> and <user>.<domain>.pub on workstations
  * public keys will be deployed exclusively on target where ansible_fqdn == <user>.<domain>
  * ssh keys can be rotated, this behavior is disabled by default
  * keypairs are created on workstations at user account creations
  * all public keys of configured keypairs are fetched back to usergroup keyring
  * private keys are never fetched to the usergroup keyring
  * other keys can be requested to be generated at user account creation
  * every public key is deployed in an exclusive fashion
  * other keys are not deployed in the internal domain (keys are exclusive)
  * to make use of other keys, the user must configure his `ssh_config` properly

### Usage

**Usergroup directory scaffolding**

To add users, you need to configure usergroups inside `group_vars` or `host_vars`.

```yaml
  usergroups:
    - name: vendorgroup
      gid: 1001
      # gid is optional
    - name: customergroup
```

You can also tweak the behavior on a per group or per machine basis. See
'Default vars'.

Then at the path defined by `groups_dir` variable (`{{ playbook_dir }}/private/groups`)
create a folder by the `usergroup name` with content such as

```bash
$ > tree
.
├── customergroup
│   └── users.yml
└── vendorgroup
    └── users.yml
```

for each of the groups you declared in `usergroups`. Other missing
directories inside the group directory will be created by the play.

**Usergroup members configuration**

In each group you will have a file where you define and configure the unix
group members. See the Role Variables` section for more information on ways
to personalise a user account. Most settings in `users_defaults` can be
overridden.

```shell
$ > cat vendorgroup/users.yml
---

users:

  - name: foo
    groups:
      - adm
      - lp
      - users
    comments: 'foo account'
    shell: "/bin/zsh"
    ssh_domains:
      - company.domain

    dotfiles_dir: dotfiles
    omyzsh_dir: .oh-my-zsh
    vim_dir: .vim

    dotfiles_symlinks:
      - vimrc
      - bashrc
      - zshrc
      - gitconfig
      - git_template
      - profile
      - zprofile
      - tmux.conf
      - ansible.cfg
      - ctags
      - pypirc

  - name: bar
    ssh_domains:
      - lan
      - example.com
    comments: 'bar user'

  - name: baz
    groups:
      - users
    ssh_domains:
      - lan
      - example.org
    comments: 'baz user'
```

**User ssh_configuration**

Each user can optionaly manage their `ssh_config` with ansible. For that to happen,
you have to create a `<username>_ssh_config.yml file inside the group directory.

For example for the *foo* user above, the statements below will be transmuted into a
`~/.ssh/config` Parameters from `users_defaults['ssh_config']` are also
considered. This file is *totaly optional*. The playbook will not fail if it
is missing for any given user.

```bash
$ > cat vendorgroup/foo_ssh_config.yml
---

ssh_config:
  - Host: bitbucket.org
    User: git
    ForwardX11: no
    PreferredAuthentications: publickey
    ControlMaster: no

  - Host: github.com
    User: git
    ForwardX11: no
    PreferredAuthentications: publickey
    ControlMaster: no

  - Host: "*lb-*"
    User: archambf
    Hostname: "%h.lb.labfqdn"
    ForwardAgent: yes
    StrictHostKeyChecking: yes
    ProxyCommand: ssh -W %h:%p jumphost
```

As you might notice,

* Every key must be a valid `ssh_config` option.
* `Match` statements are supported.
* Quote strings with special chars else yaml parsing will fail


## Requirements

### Ansible version

Minimum required ansible version is 2.1.

## Role Variables

### Variables conditionally loaded

None.

### Default vars

Defaults from `defaults/main.yml`.

```yaml
# An external directory containing sensitive data (group profiles, public ssh
# keys, users's ssh_config, ...etc.
groups_dir: "{{ playbook_dir }}/private/groups"

# Will include a `debug.yml` task file which will print variable information.
users_debug: no

# Don't generate private ssh key in user accounts on every machine, consider
# agent forwarding instead.
# Use this in group_vars to toggle ssh_key creation in a group of hosts.
users_generate_ssh_keys: no

# SSH key rotation is disabled by default.
users_rotate_ssh_keys: no

# Max age of keys for ssh_rotation. This is a time specification that must be
# compatbile with the find module.
users_ssh_key_max_age: 60d

# Default ssh key domain. Default key is the concatenation of the username and
# this value. For public key to be propagated to the right machines, it should
# match the 'ansible_domain' fact and thus hint wich realm the key gives access
# to.
users_domain: ""

# Configure '/etc/skel' facility
users_configure_skeleton: no

# If yes, 'usersgroups' are exclusive. That means that all unstated unix user
# groups in play variable will deleted along with all it's members at the exception of
# group `nogroup`.
users_exclusive_usergroups: no

# List of 'usergroups' that will never be removed
users_exclusive_usergroups_exceptions:
  - vagrant
  - nogroup

# If yes, group members are exclusive. That means that all unstated group
# members in play variables will deleted at the exception of user `nobody`.
users_exclusive_groupmembers: no

# Default args for the user module and sensible defaults for other role
# features on a per user accounts basis. Override these on a per user basis
# inside the 'users.yml' file of the usergroup.
users_defaults:
  state: present
  # fixme: task should generate something random per user, register it, and send to user by mail.
  password: "changeme" # Initial user password.
  shell: "/bin/bash"
  system: no

  groups: omit
  append: yes         # Append to group

  update_password: on_create # Default to 'on_create' (will change passwd if they differ)

  # This 'home' variable is the path prefix to the directory that will contain
  # a user account. If you work on Solaris you could set this to
  # '/export/home'.
  home: '/home'

  # Module defaults
  createhome: yes     # Defaults to yes
  move_home: no       # Defaults to no
  non_unique: no      # Defaults to no

  # Set the amount of days a password can remain inactive after expiration.
  # This is passed to the 'inactive' options of 'passwd' command.
  inactive: 365

  # SSH configuration defaults.
  # fixme: task should generate something random, register it, and send to user by mail.
  ssh_key_passphrase: q1w2e3
  ssh_key_type: rsa
  ssh_key_bits: 2048

  # Homedir skeleton.
  skel:
    - '.ssh/controlmasters'
    - '.ssh/old_keys'
    - 'bin'
    - 'tmp'

  # Values for ~/.ssh/config. Those are for a "Host *" clause at the top and
  # will be applied to every users. This doesn't prevent you from having
  # multiple "Host *" statements under it that will supersede this one. I think
  # those are acceptable sane defaults.

  ssh_config:
    ServerAliveInterval: 41
    ControlPersist: 120s
    ControlMaster: auto
    ControlPath: '~/.ssh/controlmasters/%r@%h:%p'

  # This is the list of files to symlinks to your dotfiles repo. While empty,
  # you can change if you know users share a common set of dotfiles.
  dotfiles_symlinks: []

```


## Installation

### Install with Ansible Galaxy

```shell
ansible-galaxy install archf.accounts
```

Basic usage is:

```yaml
- hosts: all
  roles:
    - role: archf.accounts
```

### Install with git

If you do not want a global installation, clone it into your `roles_path`.

```shell
git clone git@github.com:archf/ansible-accounts.git /path/to/roles_path
```

But I often add it as a submdule in a given `playbook_dir` repository.

```shell
git submodule add git@github.com:archf/ansible-accounts.git <playbook_dir>/roles/accounts
```

As the role is not managed by Ansible Galaxy, you do not have to specify the
github user account.

Basic usage is:

```yaml
- hosts: all
  roles:
  - role: accounts
```


## Dependencies

None.

## Todo

  * manage sudoers
  * generate random passwords using passlib and mail'em to user

## License

BSD.

## Author Information

Felix Archambault.

---
This README was generated using ansidoc. This tool is available on pypi!

```shell
pip3 install ansidoc

# validate by running a dry-run (will output result to stdout)
ansidoc --dry-run <rolepath>

# generate you role readme file
ansidoc <rolepath>
```

You can even use it programatically from sphinx. Check it out.