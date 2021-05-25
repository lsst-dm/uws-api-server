Kubernetes Deployment
======================================

The UWS currently supports deployment on the NCSA Test Stand (NTS) and the Summit. Common parameter values are captured in the `values.yaml` file of the Helm chart, while environment-specific values (primarily related to persistent volume configuration) are captured by `values-nts.yaml` and `values-summit.yaml`.

ArgoCD
------------------------------

Deployments are managed by the ArgoCD instances running on the two clusters:

```
Summit: https://summit-lsp.lsst.codes/argo-cd/applications/uws
NTS:    https://lsst-argocd-nts-efd.ncsa.illinois.edu/argo-cd/applications/uws
```
Credentials to access these ArgoCD instances is provided via the `https://lsstit.1password.com` password manager account.

An example of the ArgoCD Application manifest is shown below:

```
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: uws
  namespace: argocd
spec:
  destination:
    namespace: uws
    server: https://kubernetes.default.svc
  project: default
  source:
    helm:
      parameters:
      - name: logLevel
        value: DEBUG
      - name: image.tag
        value: latest
      valueFiles:
      - values.yaml
      - values-summit.yaml
    path: charts/uws-api-server
    repoURL: https://github.com/lsst-dm/charts
    targetRevision: master
```

Helm chart installation
---------------------------

The Helm chart for `uws-api-server` is in the Helm chart repo https://lsst-dm.github.io/charts/ (see that page for instructions on how to add the Helm repo and its charts).

To install via Helm, you can clone the source repo (https://github.com/lsst-dm/charts/) and install with 

```
helm upgrade --install -n $NAMESPACE \
  uws-api-server charts/uws-api-server/ \
  --values charts/uws-api-server/values.yaml \
  --values charts/uws-api-server/values-$CLUSTER.yaml 
```

where `values-$CLUSTER.yaml` is the values file specific to the target cluster.

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
