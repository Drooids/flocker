# Copyright Hybrid Logic Ltd.  See LICENSE file for details.

"""
Install flocker on a remote node.
"""

from pipes import quote as shell_quote
import posixpath
from textwrap import dedent
from urlparse import urljoin

ZFS_REPO = ("https://s3.amazonaws.com/archive.zfsonlinux.org/"
            "fedora/zfs-release$(rpm -E %dist).noarch.rpm")
CLUSTERHQ_REPO = ("https://storage.googleapis.com/archive.clusterhq.com/"
                  "fedora/clusterhq-release$(rpm -E %dist).noarch.rpm")


class IPCRunner(object):
    def __init__(self, username, address):
        from flocker.common import ProcessNode
        self._node = ProcessNode.using_ssh(
            host=address, port=22, username=username,
            private_key=None)

    def run(self, command):
        # Saddness of sh -c
        print self._node.get_output(['sh', '-c', command])

    def put(self, content, path):
        with self._node.run(['dd', 'of=' + path]) as f:
            f.write(content)


def _task_install_kernel(runner):
    runner.run("""
UNAME_R=$(uname -r)
PV=${UNAME_R%.*}
KV=${PV%%-*}
SV=${PV##*-}
ARCH=$(uname -m)
yum install -y https://kojipkgs.fedoraproject.org/packages/kernel/\
${KV}/${SV}/${ARCH}/kernel-devel-${UNAME_R}.rpm
""")


def _task_enable_docker(runner):
    """
    Fabric Task. Start docker and configure it to start automatically.
    """
    runner.run("systemctl enable docker.service")
    runner.run("systemctl start docker.service")


def _task_disable_firewall(runner):
    """
    Fabric Task. Disable the firewall.
    """
    runner.run('firewall-cmd --permanent --direct --add-rule ipv4 filter FORWARD 0 -j ACCEPT')  # noqa
    runner.run('firewall-cmd --direct --add-rule ipv4 filter FORWARD 0 -j ACCEPT')  # noqa


def _task_create_flocker_pool_file(runner):
    """
    Create a file-back zfs pool for flocker.
    """
    runner.run('mkdir -p /var/opt/flocker')
    runner.run('truncate --size 10G /var/opt/flocker/pool-vdev')
    runner.run('zpool create flocker /var/opt/flocker/pool-vdev')


def _task_install_flocker(
        runner,
        version=None, branch=None, distribution=None):
    """
    Fabric Task. Install flocker.

    :param str version: The version of flocker to install.
    :param str branch: The branch from which to install flocker.  If this isn't
        provided, install from the release repository.
    :param str distribution: The distribution the node is running.
    """
    runner.run("yum install -y " + ZFS_REPO)
    runner.run("yum install -y " + CLUSTERHQ_REPO)

    # FIXME: Suppport staging build server
    build_server = 'http://build.clusterhq.com/'
    if branch:
        result_path = posixpath.join(
            '/results/omnibus/', branch, distribution)
        base_url = urljoin(build_server, result_path)
        repo = dedent(b"""
            [clusterhq-build]
            name=clusterhq-build
            baseurl=%s
            gpgcheck=0
            enabled=0
            """) % (base_url,)
        runner.put(repo, '/etc/yum.repos.d/clusterhq-build.repo')
        branch_opt = ['--enablerepo=clusterhq-build']
    else:
        branch_opt = []

    if version:
        # FIXME flocker -> admin dependency
        from admin.release import make_rpm_version
        rpm_version = "%s-%s" % make_rpm_version(version)
        if rpm_version.endswith('.dirty'):
            rpm_version = rpm_version[:-len('.dirty')]
        package = 'clusterhq-flocker-node-%s' % (rpm_version,)
    else:
        package = 'clusterhq-flocker-node'

    command = ["yum", "install"] + branch_opt + ["-y", package]
    runner.run(" ".join(map(shell_quote, command)))


def _task_install(
        runner,
        version=None, branch=None, distribution=None):
    """
    Fabric Task. Configure a node to run flocker.
    """
    _task_install_kernel(runner)
    _task_install_flocker(
        runner,
        version=version, branch=branch, distribution=distribution)
    _task_enable_docker(runner)
    _task_disable_firewall(runner)
    _task_create_flocker_pool_file(runner)


def install(nodes, username, kwargs):
    """
    Install flocker on the given nodes.

    :param username: Username to connect as.
    :param dict kwargs: Addtional arguments to pass to ``_task_install``.
    """
    for address in nodes:
        runner = IPCRunner(username, address)
        _task_install(runner, **kwargs)
