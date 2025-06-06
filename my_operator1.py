# operator.py
import kopf
import kubernetes
import asyncio

MAX_REPLICAS = 10
MIN_REPLICAS = 2

@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    # settings.posting.level = "INFO"
    pass

@kopf.on.create('myapps.example.com', 'v1', 'mydeployments')
def create_fn(spec, name, namespace, **kwargs):
    kubernetes.config.load_incluster_config()
    apps_v1 = kubernetes.client.AppsV1Api()

    replicas = spec.get('replicas', 1)
    deployment = kubernetes.client.V1Deployment(
        metadata=kubernetes.client.V1ObjectMeta(name=name),
        spec=kubernetes.client.V1DeploymentSpec(
            replicas=replicas,
            selector=kubernetes.client.V1LabelSelector(
                match_labels={'app': name}
            ),
            template=kubernetes.client.V1PodTemplateSpec(
                metadata=kubernetes.client.V1ObjectMeta(labels={'app': name}),
                spec=kubernetes.client.V1PodSpec(containers=[
                    kubernetes.client.V1Container(
                        name='nginx',
                        image='nginx'
                    )
                ])
            )
        )
    )

    apps_v1.create_namespaced_deployment(namespace=namespace, body=deployment)

@kopf.timer('myapps.example.com', 'v1', 'mydeployments', interval=30.0)
async def scale_fn(spec, name, namespace, **kwargs):
    kubernetes.config.load_incluster_config()
    apps_v1 = kubernetes.client.AppsV1Api()
    try:
        deployment = apps_v1.read_namespaced_deployment(name=name, namespace=namespace)
        current = deployment.spec.replicas
        if current < MAX_REPLICAS:
            new_replicas = current + 1
        else:
            new_replicas = MIN_REPLICAS

        deployment.spec.replicas = new_replicas
        apps_v1.patch_namespaced_deployment(name=name, namespace=namespace, body=deployment)
    except Exception as e:
        print(f"Scaling failed: {e}")
