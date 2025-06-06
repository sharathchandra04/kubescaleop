import kopf
import kubernetes
import asyncio

# Constants
DEPLOYMENT_NAME = "nginx-autoscaler"
NAMESPACE = "default"

@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    settings.posting.level = 'INFO'
    settings.watching.server_timeout = 60
    settings.watching.client_timeout = 120

@kopf.on.create('mydeployments.myapps.example.com')
async def create_fn(spec, name, namespace, logger, **kwargs):
    replicas = spec.get('replicas', 1)
    api = kubernetes.client.AppsV1Api()

    deployment = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {"name": DEPLOYMENT_NAME, "namespace": namespace},
        "spec": {
            "replicas": replicas,
            "selector": {"matchLabels": {"app": "nginx"}},
            "template": {
                "metadata": {"labels": {"app": "nginx"}},
                "spec": {
                    "containers": [{
                        "name": "nginx",
                        "image": "nginx",
                        "ports": [{"containerPort": 80}]
                    }]
                },
            },
        },
    }

    api.create_namespaced_deployment(namespace=namespace, body=deployment)
    logger.info(f"Deployment {DEPLOYMENT_NAME} created with {replicas} replicas.")

    # Start background task
    asyncio.create_task(scale_loop(logger))


async def scale_loop(logger):
    apps_api = kubernetes.client.AppsV1Api()
    replicas = 1
    increasing = True

    while True:
        await asyncio.sleep(30)

        try:
            dep = apps_api.read_namespaced_deployment(name=DEPLOYMENT_NAME, namespace=NAMESPACE)
            replicas = dep.spec.replicas

            if increasing:
                replicas += 1
                if replicas >= 10:
                    increasing = False
            else:
                replicas = 2
                increasing = True

            dep.spec.replicas = replicas
            apps_api.patch_namespaced_deployment(name=DEPLOYMENT_NAME, namespace=NAMESPACE, body=dep)
            logger.info(f"Updated deployment to {replicas} replicas.")
        except Exception as e:
            logger.error(f"Error scaling deployment: {e}")
