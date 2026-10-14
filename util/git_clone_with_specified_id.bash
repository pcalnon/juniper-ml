#!/usr/bin/env bash


# this is how you git clone a repo while specifying the identity file explicitly
#
GIT_SSH_COMMAND="ssh -i ${HOME}/.ssh/id_ed25519_github_juniper-k8s" git clone git@github.com:pcalnon/juniper-k8s.git
