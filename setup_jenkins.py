import os
import yaml
import re
import requests
import subprocess

from jenkinsapi.credential import UsernamePasswordCredential
from jenkinsapi.credential import SSHKeyCredential
from jenkinsapi.credential import SecretTextCredential
from jenkinsapi.jenkins import Jenkins
from jenkinsapi.utils.crumb_requester import CrumbRequester
from six.moves import urllib


class JenkinsConnection(object):
    def __init__(self, jenkins_url, username, api_token):
        self.jenkins_url = jenkins_url
        self.username = username
        self.api_token = api_token
        self.jenkins = self.get_jenkins()

    def get_jenkins(self):
        """
        Figure out if jenkins needs crumbs or not and return correct Jenkins instance.
        """
        jenkins_url = self._get_jenkins_url()
        r = requests.post(jenkins_url)
        if r.status_code == 403:  # Probably because of missing crumb.
            requester = CrumbRequester(baseurl=jenkins_url,
                                       username=self.username,
                                       password=self.api_token)
            return Jenkins(jenkins_url, self.username, self.api_token, requester=requester)
        else:
            return Jenkins(jenkins_url, self.username, self.api_token)

    def _get_jenkins_url(self):
        """
        To post to Jenkins secured with CSRF (i.e. needing crumbs) jenkinsapi
        needs the username:password combination in the url.
        """
        # https://stackoverflow.com/questions/12368357/parsing-a-url-overriding-parts-and-putting-it-back-together-in-python
        netloc_regex = re.compile(r"(?:([^:]+)(?::(.*))?@)?([^:]+)(?::([\d]+))?")
        scheme, netloc, path, params, query, fragment = urllib.parse.urlparse(self.jenkins_url)
        username, password, host, port = netloc_regex.search(netloc).groups()
        auth = ":".join(filter(None, (self.username, self.api_token)))
        address = ":".join(filter(None, (host, port)))
        netloc = "@".join(filter(None, (auth, address)))
        return urllib.parse.urlunparse((scheme, netloc, path, params, query, fragment))


class CredentialManager(object):
    def __init__(self, jenkins):
        self.jenkins = jenkins

    def create_username_password(self, username, password, description, credential_id='', **kwargs):
        """
        Creates a global username password combination.
        Description must be unique.
        """
        creds = self.jenkins.credentials
        cred_dict = {
            'description': description,
            'userName': username,
            'password': password,
            'credential_id': credential_id
        }
        creds[description] = UsernamePasswordCredential(cred_dict)

    def create_ssh_private_key(self, username, private_key, description, credential_id='', passphrase='', **kwargs):
        """
        Creates a global ssh key file.
        Description must be unique.
        """
        if os.path.exists(private_key):
            # Read in a local ssh key.
            # jenkinsapi handles potential paths to ssh key on jenkins master for us.
            with open(private_key) as f:
                private_key = f.read()
        creds = self.jenkins.credentials
        cred_dict = {
            'description': description,
            'userName': username,
            'passphrase': passphrase,
            'credential_id': credential_id,
            'private_key': private_key
        }
        creds[description] = SSHKeyCredential(cred_dict)

    def create_secret_text(self, secret, description, credential_id='', **kwargs):
        creds = self.jenkins.credentials
        cred_dict = {
            'description': description,
            'credential_id': credential_id,
            'secret': secret
        }
        creds[description] = SecretTextCredential(cred_dict)


class JobManager(object):
    def __init__(self, jenkins, job_path):
        self.jenkins = jenkins
        self.job_path = job_path
        self.job_xml = self.job_to_xml()
        self.load_job_xml()

    def job_to_xml(self):
        cmd = ['jenkins-jobs', 'test', self.job_path]
        return subprocess.check_output(cmd, shell=False)

    def load_job_xml(self):
        self.jenkins.create_job('seed', self.job_xml)


def load_secrets(credentials, jenkins):
    cm = CredentialManager(jenkins.jenkins)
    for cred in credentials:
        if cred['type'] == 'private_key':
            cm.create_ssh_private_key(**cred)
        elif cred['type'] == 'username_password':
            cm.create_username_password(**cred)
        elif cred['type'] == 'secret_text':
            cm.create_secret_text(**cred)


def main():
    config = get_config()
    jenkins = JenkinsConnection(**config.get('jenkinsCredentials'))
    credentials = config.get('credentials', [])
    #load_secrets(credentials, jenkins.jenkins)
    JobManager(jenkins.jenkins, job_path='job_builder.yml')


def get_config():
    """
    Returns config as dictionary
    :return:
    """
    with open('just-dockerfiles.yml') as conffile:
        return yaml.load(conffile)


if __name__ == '__main__':
    main()
