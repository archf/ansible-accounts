# ansible-accounts

A role to create and configure user accounts and groups on a host.

## Ansible requirements

### Ansible version

Minimum required ansible version is 2.3.

### Ansible role dependencies

None.

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
## User guide

### requirements:
  This roles contains tasks relying on the `synchronize` module (rsync) and
  therefore it requires the `openssh` daemon to be running.

  However, if no underlying connection is not `ssh`, it will fall back to the
  copy module.

### Introduction

**Usergroups**

This role works in a usergroups paradigm. As your coworkers also needs to
login on the same servers, user accounts are configured by adding one or
multiple usergroups composed of one or more individual users that will end up
attached to the unix group named after the usergroup name. Phew!

There is also 'noadmin' mode for when you have no control over the remote
machine. You can use this on the restricted machines to deploy your public
ssh keys and your dotfiles. You will be touching **only your account**

**SSH keys management**

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
    # gid is optional
    gid: 1001
    # create vendorgroup file inside /etc/sudoers.d
    sudoers: yes
    # nopasswd is optional
    nopasswd: ALL

  - name: customergroup
```

You can also tweak the behavior on a per group or per machine basis. See
variables in 'Default vars' .

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
    comments: 'foo account'
    groups:
      - adm
      - lp
      - users
    shell: "/bin/zsh"

    # optional
    ssh_domains:
      - company.domain

    # optional
    dotfiles_dir: dotfiles
    vim_dir: .vim

    # optional
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
    comments: 'bar user'
    ssh_domains:
      - lan
      - example.com

  - name: baz
    comments: 'baz user'
    groups:
      - users
    ssh_domains:
      - lan
      - example.org
```

**When remote_user is different than local_user **

see `users_usermap` in `defaults/main.yml`

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

**Using the 'noadmin' mode**

For this restricted mode, just set the `users_noadmin' boolean to yes|True
either on the cli (`-e users_noadmin=True`) or in your playbook variables.


## Role Variables

Variables are divided in three types.

The [default vars](#default-vars) section shows you which variables you may
override in your ansible inventory. As a matter of fact, all variables should
be defined there for explicitness, ease of documentation as well as overall
role manageability.

The [mandatory variables](#mandatory-variables) section contains variables that
for several reasons do not fit into the default variables. As name implies,
they must absolutely be defined in the inventory or else the role will
fail. It is a good thing to avoid reach for these as much as possible and/or
design the role with clear behavior when they're undefined.

The [context variables](#context-variables) are shown in section below hint you
on how runtime context may affects role execution.

### Default vars

Role default variables from `defaults/main.yml`.

```yaml
# An external directory containing sensitive data (group profiles, public ssh
# keys, users's ssh_config, ...etc.
groups_dir: "{{inventory_dir}}/private/groups"

users_usergroups: []

# If you have no admin rights on the remote machine and you only want to deploy
# your dotfiles and/or your ssh keys, turn on this option. It will only touch
# your account (i.e: deploy your ssh keys and sync your dotfiles)
users_noadmin: no

# Force expiration of new user's so they are prompted to change it on first
# login.
users_expire_passwords: no

# Don't generate private ssh key in user accounts on every machine, consider
# agent forwarding instead. Use this in group_vars to toggle ssh_key creation
# in a group of hosts.
users_generate_ssh_keys: no

# SSH key rotation is disabled by default. Enabling this implicitly enables
# users_generate_ssh_keys.
users_rotate_ssh_keys: no

# Exclusive ssh keys on remote accounts. This is fed to the authorized_key
# module.
users_exclusive_ssh_keys: no

# Max age of keys for ssh_rotation. This is a time specification that must be
# compatbile with the find module.
users_ssh_key_max_age: 60d

# Default ssh key domain. Default key name is the concatenation of the username
# and this value. For public key to be propagated to the right machines, it
# should match the 'ansible_domain' fact and thus hint wich realm the key gives
# access to.
users_default_domain: ""

# Configure '/etc/skel' facility. Useful prior accounts creation. Doing it on
# lot of user home directory after they created is costly. This will add
# directories as defined in users_defaults['skel'].
users_gen_skel: no

# Enable this to ensure already created home matches de /etc/skel structure.
# This task can be somewhat slow when managing lots of users on a large
# inventory. This behavior is rather invasive and probably more suitable for
# personal usage and/or when you have no control over /etc/skel.
users_skel_homedir: no

# If yes, 'usergroups' are exclusive. That means that all unstated unix
# usergroups in play variable will be deleted along with all it's members at
# the exception of group `nogroup`.
users_exclusive_usergroups: no

# List of 'usergroups' that will never be removed.
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
  shell: "/bin/bash"
  system: no

  groups: omit
  append: yes         # Append to group

  # Default to 'on_create' (will change passwd if they differ). Could also be
  # set to 'always'.
  update_password: 'on_create'

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

  # This is the list of files in your dotfiles_dir you do not want to rsync
  # to the remote host.
  dotfiles_rsync_exclude:
    - americano
    - i3
    - zsh-autosuggestion
    - debug-refs
    - gnupg
    - hexchat
    - win*
    - wireshark
    - _vimrc
    - f-desktop.prf

    # directories for building tmux, vim, openssh from source
    - tmux/tmux-?.?
    - vim.d/vim
    - openssh

# Sometimes, remote user account doesn't match the local one. That happens for
# instance when host is 'mostly' controlled by your customer. Fill this dict
# with keys such as { '<remote_username>' : '<local userneame>'}.
users_usermap: {}

# You can have shared by multiple users. Define this variable in `users.yml`
# to have usergroup defaults different than `users_defaults`.
usergroup_defaults:
  passwd: ''

### omited parameters

# By default, the first make target is ran but you way want to override. Could
# be useful to if hosts have no www access. This is fed to the make module
# target argument.
# users_dotfiles_makefile_target: ''

# Include debugging tasks that prints variable information when adding and
# removing unix groups.
groupadd_debug: no
groupdel_debug: no

```

### Mandatory variables

None.

### Context variables

None.


## Todo

You want to contribute? Here's a wishlist:

  * generate random passwords using passlib and mail'em to user

Consider opening an issue to share your intent and avoid work duplication!

## License

BSD.

## Author Information

Felix Archambault.

---
Please do not edit this file. This role `README.md` was generated using the
'ansidoc' python tool available on pypi!

*Installation:*

```shell
pip3 install ansidoc
```

*Basic usage:*

Validate output by running a dry-run (will output result to stdout)
```shell
ansidoc --dry-run <rolepath>
```

Generate you role readme file. Will write a `README.md` file under
`<rolepath>/README.md`.
```shell
ansidoc <rolepath>
```

Also usable programatically from Sphinx.