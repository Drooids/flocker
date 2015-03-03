.. _api:

================
Flocker REST API
================

We are currently in the process of developing an external HTTP-based REST API for Flocker.
While this API is not yet directly accessible in a standard Flocker setup, the documentation below will give a sense of what will eventually be available.


Installation
============

To allow remote access to the control agent REST API, and for agent connections,

.. task:: open_control_firewall

For more details on configuring the firewall, see Fedora's `FirewallD documentation <https://fedoraproject.org/wiki/FirewallD>`_.

API Details
===========

In general the API allows for modifying the desired configuration of the cluster.
A successful response indicates a change in configuration, not a change to cluster state.
Convergence agents will then take the necessary actions and eventually the cluster's state will match the requested configuration.

.. autoklein:: flocker.control.httpapi.DatasetAPIUserV1
    :schema_store_fqpn: flocker.control.httpapi.SCHEMAS
    :prefix: /v1
    :examples_path: api_examples.yml
