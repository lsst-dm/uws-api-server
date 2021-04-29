Kubernetes Deployment
======================================

The UWS currently supports deployment on the NCSA Test Stand (NTS) or the NCSA Integration cluster (INT). The deployments are cluster-specific due to the GPFS and NFS persistent volumes that must be manually created by the sysadmin.

Persistent Volumes
------------------------------

INT cluster:

|PVC name             |Mount point                                         |
|:--------------------|:---------------------------------------------------|
|nfs-scratch-pvc     |`/scratch/uws `                                      |
|nfs-data-pvc        |`/offline/teststand     `                            |
|nfs-oods-comcam-pvc |`/data/lsstdata/NTS/comcam/oods/gen3butler/repo     `|
|nfs-oods-auxtel-pvc |`/data/lsstdata/NTS/auxTel/oods/gen3butler/repo     `|

NTS cluster:

|PVC name             |Mount point    |
|:--------------------|:--------------|
|lsst-dm-scratch-pvc  |`/scratch/uws `|
|lsst-dm-projects-pvc |`/project     `|
|lsst-dm-repo-pvc     |`/repo        `|

kubectl access
------------------------------

A convenient method for accessing the Kubernetes cluster is described below. Create an SSH tunnel to the target Kubernetes API server using
```
ssh -L 127.0.0.1:6443:141.142.X.Y:6443 lsst-login.ncsa.illinois.edu
```
where `141.142.X.Y` is the IP address of the API server.

Create a kubeconfig `$HOME/.kube/config.$TARGET_CLUSTER.proxy` using your existing kubeconfig as shown below, where the `insecure-skip-tls-verify: true` is necessary due to the SSH tunnel. Replace `$TARGET_CLUSTER` with the k8s cluster name, `$TARGET_NAMESPACE` with the deployment namespace on that cluster, and `$USERNAME` with your username.
```
apiVersion: v1
clusters:
- cluster:
    insecure-skip-tls-verify: true
    server: https://127.0.0.1:6443
  name: $TARGET_CLUSTER
contexts:
- context:
    cluster: $TARGET_CLUSTER
    namespace: $TARGET_NAMESPACE
    user: $USERNAME
  name: cluster-user@$TARGET_CLUSTER
current-context: cluster-user@$TARGET_CLUSTER
kind: Config
preferences: {}
users:
- name: $USERNAME
  user:
    client-certificate-data: **********
    client-key-data: **********
```

Activate the kubeconfig prior to executing `helm` or `kubectl` with:
``` 
export KUBECONFIG="$HOME/.kube/config.$TARGET_CLUSTER.proxy"
```

Helm chart installation
---------------------------

The Helm chart for `uws-api-server` is in the Helm repo https://lsst-dm.github.io/charts/ (see that page for instructions on how to add the Helm repo and its charts).

During development, you can clone the source repo (https://github.com/lsst-dm/charts/) and install with 
```
helm upgrade --install -n $NAMESPACE \
  uws-api-server charts/uws-api-server/ \
  --values charts/uws-api-server/values-$CLUSTER.yaml 
```

where `values-$CLUSTER.yaml` is the values file specific to the target cluster.
