# Standard Library
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

import kubernetes
from kubernetes.client.exceptions import ApiException
from urllib3.exceptions import ConnectionError

# Sematic
from sematic.config import SettingsVar, get_user_settings
from sematic.docker_images import CONTAINER_IMAGE_ENV_VAR
from sematic.resolvers.resource_requirements import ResourceRequirements
from sematic.scheduling.external_job import KUBERNETES_JOB_KIND, ExternalJob, JobType
from sematic.utils.retry import retry

logger = logging.getLogger(__name__)
_kubeconfig_loaded = False


@dataclass
class KubernetesExternalJob(ExternalJob):

    # See
    # github.com/kubernetes-client/python/blob/master/kubernetes/docs/V1JobStatus.md
    # and: https://kubernetes.io/docs/concepts/workloads/controllers/job/

    # this is the "active" property.
    pending_or_running_pod_count: int
    succeeded_pod_count: int
    has_started: bool
    still_exists: bool

    @property
    def run_id(self) -> str:
        return self.kubernetes_job_name.split("-")[-1]

    @property
    def namespace(self) -> str:
        return self.external_job_id.split("/")[0]

    @property
    def job_type(self) -> JobType:
        return JobType[self.kubernetes_job_name.split("-")[1]]

    @property
    def kubernetes_job_name(self) -> str:
        return self.external_job_id.split("/")[-1]

    @classmethod
    def make_external_job_id(
        self, run_id: str, namespace: str, job_type: JobType
    ) -> str:
        job_name = "-".join(("sematic", job_type.value, run_id))
        return f"{namespace}/{job_name}"

    def is_active(self) -> bool:
        # According to the docs:
        # github.com/kubernetes-client/python/blob/master/kubernetes/docs/V1JobStatus.md
        # a job's "active" field holds the number of pending or running pods.
        # This should be a more reliable measure of whether the job is still
        # active than the number of succeeded or failed pods, as during pod
        # evictions (which don't stop the job completely, but do stop the pod),
        # a pod can briefly show up as failed even when another one is
        # going to be scheduled in its place.
        if not self.has_started:
            return True
        if not self.still_exists:
            return False
        return self.succeeded_pod_count == 0 and self.pending_or_running_pod_count > 0


def load_kube_config():
    global _kubeconfig_loaded
    if _kubeconfig_loaded:
        return
    try:
        kubernetes.config.load_kube_config()  # type: ignore
    except kubernetes.config.config_exception.ConfigException as e1:  # type: ignore
        try:
            kubernetes.config.load_incluster_config()  # type: ignore
        except kubernetes.config.config_exception.ConfigException as e2:  # type: ignore # noqa: E501
            raise RuntimeError("Unable to find kube config:\n{}\n{}".format(e1, e2))
    _kubeconfig_loaded = True


@retry(exceptions=(ApiException, ConnectionError), tries=3, delay=5, jitter=2)
def refresh_job(job):
    load_kube_config()
    if not isinstance(job, KubernetesExternalJob):
        raise ValueError(
            f"Expected a {KubernetesExternalJob.__name__}, got a {type(job).__name__}"
        )
    try:
        k8s_job = kubernetes.client.BatchV1Api().read_namespaced_job_status(
            name=job.kubernetes_job_name, namespace=job.namespace
        )
    except ApiException as e:
        if e.status == 404:
            if not job.has_started:
                return job  # still hasn't started
            else:
                job.still_exists = False
                return job
        raise e
    job.has_started = True
    job.pending_or_running_pod_count = (
        k8s_job.status.active if k8s_job.status.active is not None else 0
    )
    job.succeeded_pod_count = (
        k8s_job.status.succeeded if k8s_job.status.succeeded is not None else 0
    )


def _schedule_kubernetes_job(
    name: str,
    image: str,
    environment_vars: Dict[str, str],
    namespace: str,
    resource_requirements: Optional[ResourceRequirements] = None,
    args: Optional[List[str]] = None,
):
    load_kube_config()
    args = args if args is not None else []
    node_selector = {}
    if resource_requirements is not None:
        node_selector = resource_requirements.kubernetes.node_selector
        logger.debug("kubernetes node_selector %s", node_selector)

    job = kubernetes.client.V1Job(  # type: ignore
        api_version="batch/v1",
        kind="Job",
        metadata=kubernetes.client.V1ObjectMeta(name=name),  # type: ignore
        spec=kubernetes.client.V1JobSpec(  # type: ignore
            template=kubernetes.client.V1PodTemplateSpec(  # type: ignore
                spec=kubernetes.client.V1PodSpec(  # type: ignore
                    node_selector=node_selector,
                    containers=[
                        kubernetes.client.V1Container(  # type: ignore
                            name=name,
                            image=image,
                            args=args,
                            env=[
                                kubernetes.client.V1EnvVar(  # type: ignore
                                    name=CONTAINER_IMAGE_ENV_VAR,
                                    value=image,
                                )
                            ]
                            + [
                                kubernetes.client.V1EnvVar(  # type: ignore
                                    name=name,
                                    value=value,
                                )
                                for name, value in environment_vars.items()
                            ],
                            volume_mounts=[],
                            resources=None,
                        )
                    ],
                    volumes=[],
                    tolerations=[],
                    restart_policy="Never",
                ),
            ),
            backoff_limit=0,
            ttl_seconds_after_finished=3600,
        ),
    )

    kubernetes.client.BatchV1Api().create_namespaced_job(  # type: ignore
        namespace=namespace, body=job
    )


def schedule_run_job(
    run_id: str,
    image: str,
    user_settings: Dict[str, str],
    resource_requirements: Optional[ResourceRequirements] = None,
    try_number: int = 0,
) -> ExternalJob:
    # "User" in this case is the server.
    namespace = get_user_settings(SettingsVar.KUBERNETES_NAMESPACE)
    external_job_id = KubernetesExternalJob.make_external_job_id(
        run_id, namespace, JobType.worker
    )
    external_job = KubernetesExternalJob(
        kind=KUBERNETES_JOB_KIND,
        try_number=try_number,
        external_job_id=external_job_id,
        pending_or_running_pod_count=1,
        succeeded_pod_count=0,
        has_started=False,
        still_exists=True,
    )
    logger.info("Scheduling job %s", external_job.kubernetes_job_name)
    args = ["--run_id", run_id, "--resolve"]

    _schedule_kubernetes_job(
        name=external_job.kubernetes_job_name,
        image=image,
        environment_vars=user_settings,
        namespace=namespace,
        resource_requirements=resource_requirements,
        args=args,
    )
    return external_job
