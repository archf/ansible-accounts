#!/bin/sh

# this is a ssh wrapper meant to be called by ansible. It extends ansible to
# allow creation of ssh key pairs in non remote_user accouts and should be invoked
# as root (while -> remote_user: root). Ownerships and permisions are set properly.

# default passphrase value
PASSPHRASE=""

# help menu
usage() {
  echo "Generate a ssh key inside a user account and set permissons and
  ownership properly.

  Options:
  -d <home directory path> 'this includes the account name'
  -u <user account name>
  -k <ssh key name suffixe> the user account name is prepended before this
  -p <passphrase>"
}

# extract options & args
while getopts "d:u:k:p:" opt; do
  case $opt in
    h ) usage
      exit 1;;
    d ) HOMEDIR="$OPTARG";;
    u ) USER="$OPTARG";;
    p ) PASSPHRASE="$OPTARG";;
    k ) KEY="$OPTARG";;
    \? ) usage
      exit 1;;
    * ) usage
      exit 1;;
  esac
done

# echo "$USER"
# echo "$PASSPHRASE"
# echo "$KEY"

# extract the user from the homedir path
USER=$(echo $HOMEDIR | awk -F '/' '{ print $NF }')



if [ ! -e "$HOMEDIR"/.ssh/$KEY ]
then
  HOST=$(hostname)
  ssh-keygen -q -t rsa -N "$PASSPHRASE" -f \
    "$HOMEDIR"/.ssh/"$KEY" -C "$USER"@$HOST

  # adjust ownership & perms
  chown $USER:$USER "$HOMEDIR"/.ssh/$KEY*
  chmod 600 "$HOMEDIR"/.ssh/$KEY
  chmod 644 "$HOMEDIR"/.ssh/"$KEY".pub
fi
  # HOST=$(hostname)
  # ssh-keygen -q -t rsa -N "$PASSPHRASE" -f \
  #   "$HOMEDIR"/"$USER"/.ssh/"$USER""$KEY" -C "$USER"@$HOST

  # # adjust ownership & perms
  # chown $USER:$USER "$HOMEDIR"/$USER/.ssh/$KEY*
  # chmod 600 "$HOMEDIR"/$USER/.ssh/$KEY
  # chmod 644 "$HOMEDIR"/$USER/.ssh/"$KEY".pub
