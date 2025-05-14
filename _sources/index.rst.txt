UWS API Server Documentation
============================================

This repo implements a Universal Worker Service (UWS) API server for the Vera C. Rubin Observatory Legacy Survey of Space and Time (LSST) to provide an asynchronous job management system that follows the `Universal Worker Service Pattern defined by the International Virtual Observatory Alliance <https://www.ivoa.net/documents/UWS/>`_.

.. Developer Quick Start
.. ------------------------------

.. admonition:: Quick Start

    **Developer Quick Start**

    If you are a developer new to the UWS system, get started quickly by following these steps:

    1. Familiarize yourself with the :ref:`system-components`.
    2.

.. toctree::
    :maxdepth: 2
    :caption: Contents:

    api/Readme
    ocps_prototype
    Development
    Deployment

.. _system-components:

System components
------------------------------

The OCPS system consists of several components.

Docker images
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The source code repo https://github.com/lsst-dm/uws-api-server is used to build the Docker image of the UWS API server. GitHub Actions are used to automatically build the ``latest`` tagged image when commits are pushed to the ``master`` branch (and ``dev`` branch commits build ``dev`` tagged images).

Kubernetes deployment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The Kubernetes deployment is defined by a Helm chart in the Helm repo https://lsst-dm.github.io/charts. Releases of this Helm chart are deployed on the NTS and Summit clusters via ArgoCD apps. See :doc:`Deployment` for details.

Documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This documentation is automatically built and published using GitHub Actions and GitHub pages. There is a workflow definition file in ``/.github/workflows/`` that creates a GitHub Action that triggers the build process whenever there is a push to the `master` branch. See :doc:`Development` for details.


Links
------------------------------

* `DMTN-133: OCS driven data processing <https://dmtn-133.lsst.io>`_
* `DMTN-143: Image Capture Simplification <https://dmtn-143.lsst.io>`_
* `International  Virtual  Observatory  Alliance: Universal Worker Service Pattern <https://www.ivoa.net/documents/UWS/>`_
    The Universal Worker Service (UWS) pattern defines how to manage asynchronous execution of jobs on a service. Any application of the pattern defines a family of related services with a common service contract. Possible uses of the pattern are also described.
* https://github.com/aipescience/uws-client
* https://github.com/kristinriebe/uws-validator
