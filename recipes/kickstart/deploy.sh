#!/usr/bin/env bash

function cleanup () {
    # We stop the instance (or we keep the instance in case we debug interactively)
    if [ "$DEBUG" == "True" ]; then
        echo "Exiting, $HOST is still alive";
    else
        echo "Cleaning up test-instance";
        ifbcloud stop -n jenkins_kickstart;
    fi
}

trap cleanup ERR

# We fail on first error
set -e

# We first need a new IFB instance:

unset HOST
HOST=$(ifbcloud start -n jenkins_kickstart -t c3.medium)  # The credentials come via ENV VARS
export BIOBLEND_GALAXY_URL=http://$HOST/

# Enter TARGET directory
cd "$TARGET_PATH"

# Get the specified roles
ansible-galaxy install -r requirements_roles.yml -p roles

# Write out a test-inventory
echo "[kickstart]" > kickstart_inventory
echo "$HOST" >> kickstart_inventory

# Generate the ansible-vault password file
echo "$ANSIBLE_VAULT_PASSWORD" > vault_pass.txt

# Run playbook that installs IFB ssh key
ansible-playbook -c local -i "localhost," -vvvv --vault-password-file vault_pass.txt setup/copy_ssh_key.yml

# Sleep a minute to give the machine time to boot up
sleep 60

# Launch the playbook
export ANSIBLE_HOST_KEY_CHECKING=False
ansible-playbook -u root -vvvv --private-key=/root/.ssh/id_rsa  -i kickstart_inventory galaxy.yml

# Test that galaxy is available and run bioblend test-suite against new galaxy instance
curl http://"$HOST"/api/version | grep version_major
cd /tmp/ansible/bioblend/
python /tmp/ansible/bioblend/setup.py nosetests -e 'test_download_dataset|test_upload_from_galaxy_filesystem|test_get_datasets|test_datasets_from_fs'
