""""Argo Workflow for testing notebook-server-jupyter-tensorflow OCI images"""
from kubeflow.kubeflow.ci import workflow_utils
from kubeflow.testing import argo_build_util


class Builder(workflow_utils.ArgoTestBuilder):
    def __init__(self, name=None, namespace=None, bucket=None,
                 test_target_name=None, **kwargs):
        super().__init__(name=name, namespace=namespace, bucket=bucket,
                         test_target_name=test_target_name, **kwargs)

    def build(self):
        """Build the Argo workflow graph"""
        workflow = self.build_init_workflow(exit_dag=False)
        task_template = self.build_task_template(
            mem_override="8Gi", deadline_override=6000)

        # Test building notebook-server-jupyter-tensorflow images using Kaniko
        dockerfile = ("%s/components/example-notebook-servers"
                      "/jupyter-tensorflow/cpu.Dockerfile") % self.src_dir
        context = "dir://%s/components/example-notebook-servers/jupyter-tensorflow/" % self.src_dir  # noqa: E501
        destination = "notebook-server-jupyter-tensorflow-cpu-test"

        kaniko_task = self.create_kaniko_task(
            task_template, dockerfile, context, destination, no_push=True)
        argo_build_util.add_task_to_dag(workflow,
                                        workflow_utils.E2E_DAG_NAME,
                                        kaniko_task, [self.mkdir_task_name])

        dockerfile_cuda = (
            "%s/components/example-notebook-servers"
            "/jupyter-tensorflow/cuda.Dockerfile") % self.src_dir
        destination_cuda = "notebook-server-jupyter-tensorflow-cuda-test"

        kaniko_task_cuda = self.create_kaniko_task(
            task_template, dockerfile_cuda, context, destination_cuda,
            no_push=True)
        argo_build_util.add_task_to_dag(
            workflow, workflow_utils.E2E_DAG_NAME, kaniko_task_cuda, [
                self.mkdir_task_name])

        # Set the labels on all templates
        workflow = argo_build_util.set_task_template_labels(workflow)

        return workflow


def create_workflow(name=None, namespace=None, bucket=None, **kwargs):
    """
    Args:
        name: Name to give to the workflow. This can also be used to name
              things associated with the workflow.
    """
    builder = Builder(name=name, namespace=namespace, bucket=bucket, **kwargs)

    return builder.build()
