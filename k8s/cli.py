# k8s_cli.py
import click
import json
from k8s_manager import K8sManager

@click.group()
def cli():
    """Stable Diffusion Multiplayer K8s 管理工具"""
    pass

@cli.command()
def deploy():
    """部署所有资源"""
    k8s = K8sManager()
    k8s.deploy_all()

@cli.command()
def status():
    """查看集群状态"""
    k8s = K8sManager()
    k8s.status_report()

@cli.command()
@click.argument('deployment_name')
@click.argument('replicas', type=int)
def scale(deployment_name, replicas):
    """扩缩容部署"""
    k8s = K8sManager()
    k8s.scale_deployment(deployment_name, replicas)

@cli.command()
@click.argument('deployment_name')
def restart(deployment_name):
    """重启部署"""
    k8s = K8sManager()
    k8s.restart_deployment(deployment_name)

@cli.command()
@click.argument('pod_name')
@click.option('--container', '-c', help='容器名称')
def logs(pod_name, container):
    """获取Pod日志"""
    k8s = K8sManager()
    logs = k8s.get_pod_logs(pod_name, container)
    click.echo(logs)

@cli.command()
def pods():
    """列出所有Pod"""
    k8s = K8sManager()
    pods = k8s.get_pod_status()
    click.echo(json.dumps(pods, indent=2, default=str))

if __name__ == '__main__':
    cli()