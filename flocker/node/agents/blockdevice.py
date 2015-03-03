# -*- test-case-name: flocker.node.agents.test.test_blockdevice -*-

"""
This module implements the parts of a block-device based dataset
convergence agent that can be re-used against many different kinds of block
devices.
"""

from zope.interface import implementer
from .. import IDeployer

@implementer(IDeployer)
# @attributes(["hostname", "block_device_api"])
class BlockDeviceDeployer(object):
    """
    """
