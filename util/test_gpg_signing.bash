#!/usr/bin/env bash

echo "Validating code-signing:"
echo test | gpg --clearsign -u 93E8591643C507FF

# git config --global user.signingkey '93E8591643C507FF!'
# gpg --armor --export 93E8591643C507FF
