Kubernetes Deployment
======================================

The UWS currently supports deployment on the NCSA Test Stand (NTS) and the Summit. Common parameter values are captured in the `values.yaml` file of the Helm chart, while environment-specific values (primarily related to persistent volume configuration) are captured by `values-nts.yaml` and `values-summit.yaml`.

Version control
------------------------------

The UWS application consists of [the Helm chart defining the deployment](https://github.com/lsst-dm/charts/tree/master/charts/uws-api-server) and the Docker images run by the containers. These are synchronized using the following versioning system:

- When a stable update is made to the `uws-api-server` source code repo, the Docker image is built, tagged with an incremented version, and pushed. The repo commit is tagged with the same version. GitHub Actions automatically build the `latest` tagged image when the commit is pushed, but the specific version tags must be added and push manually via `docker tag` and `docker push`.

- When a stable update is made to the `charts` Helm chart repo, the Helm chart version is incremented and the repo commit is tagged with the same version. The ArgoCD application should then be updated to reference that Helm chart version.

ArgoCD
------------------------------

Deployments are managed by the ArgoCD instances running on the two clusters:

```
Summit: https://summit-lsp.lsst.codes/argo-cd/applications/uws
NTS:    https://lsst-argocd-nts-efd.ncsa.illinois.edu/argo-cd/applications/uws
```
Credentials to access these ArgoCD instances is provided via the `https://lsstit.1password.com` password manager account.

Examples of the ArgoCD Application manifest are shown below (production and development releases), demonstrating how the parameter values are set first by the `values.yaml` file, and then overridden by the `values-summit.yaml` file, and then overridden by the ``parameters`` section of the ``Application`` manifest itself. [Read more about overrides here](https://argo-cd.readthedocs.io/en/stable/user-guide/parameters/).

### Production

```yaml
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
      valueFiles:
      - values.yaml
      - values-summit.yaml
    path: charts/uws-api-server
    repoURL: https://github.com/lsst-dm/charts
    targetRevision: v1.2.0
```

### Development

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: 'uws-dev'
spec:
  project: default
  source:
    repoURL: 'https://github.com/lsst-dm/charts'
    path: charts/uws-api-server
    targetRevision: dev
    helm:
      valueFiles:
        - values.yaml
        - values-nts-dev.yaml
      parameters:
        - name: logLevel
          value: DEBUG
        - name: image.tag
          value: dev
  destination:
    server: 'https://kubernetes.default.svc'
    namespace: uws

```

Helm chart installation (alternative to ArgoCD)
-----------------------------------------------

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

Issues with Persistent Volumes
------------------------------------

The PV and PVC resources will not upgrade gracefully, because they are immutable when created. They must be deleted and then the ArgoCD app re-synced. However, in this process they will often get stuck in a Terminating state endlessly. To allow them to finish deleting, remove the finalizers by patching the resource definitions as shown in the example below for the PVCs. The same pattern works for the PVs.

```sh
$ kubectl get -n uws pvc -l app=uws-uws-api-server
NAME             STATUS        VOLUME                             CAPACITY   ACCESS MODES   STORAGECLASS   AGE
data-pvc         Terminating   uws-uws-api-server-data-pv         0                                        17h
home-pvc         Terminating   uws-uws-api-server-home-pv         0                                        17h
project-pvc      Terminating   uws-uws-api-server-project-pv      0                                        17h
repo-pvc         Terminating   uws-uws-api-server-repo-pv         0                                        17h
uws-server-pvc   Terminating   uws-uws-api-server-uws-server-pv   0                                        17h

$ kubectl patch -n uws pvc -p '{"metadata":{"finalizers":null}}' data-pvc home-pvc project-pvc repo-pvc uws-server-pvc
persistentvolumeclaim/data-pvc patched
persistentvolumeclaim/home-pvc patched
persistentvolumeclaim/project-pvc patched
persistentvolumeclaim/repo-pvc patched
persistentvolumeclaim/uws-server-pvc patched

```
