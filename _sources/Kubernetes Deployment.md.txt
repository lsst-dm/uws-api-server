Kubernetes Deployment
======================================

The UWS currently supports deployment on the NCSA Test Stand (NTS) or the NCSA Integration cluster ("int"). The deployments are cluster-specific due to the GPFS and NFS persistent volumes that must be manually created by the sysadmin.

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

