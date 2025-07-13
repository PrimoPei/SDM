# k8s_manager.py
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import yaml
import os
from typing import Dict, List, Optional

class K8sManager:
    def __init__(self, config_path: Optional[str] = None):
        """初始化k8s客户端"""
        if config_path:
            config.load_kube_config(config_file=config_path)
        else:
            try:
                config.load_incluster_config()  # 集群内运行
            except:
                config.load_kube_config()  # 本地运行
        
        self.v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        self.networking_v1 = client.NetworkingV1Api()
        self.autoscaling_v1 = client.AutoscalingV1Api()
        
        self.namespace = "stable-diffusion-multiplayer"
    
    def create_namespace(self):
        """创建命名空间"""
        try:
            namespace = client.V1Namespace(
                metadata=client.V1ObjectMeta(name=self.namespace)
            )
            self.v1.create_namespace(namespace)
            print(f"命名空间 {self.namespace} 创建成功")
        except ApiException as e:
            if e.status == 409:
                print(f"命名空间 {self.namespace} 已存在")
            else:
                print(f"创建命名空间失败: {e}")
    
    def apply_yaml_file(self, yaml_file: str):
        """应用YAML文件"""
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                docs = yaml.safe_load_all(f)
                for doc in docs:
                    if doc:
                        self._apply_resource(doc)
        except Exception as e:
            print(f"应用YAML文件 {yaml_file} 失败: {e}")
    
    def _apply_resource(self, resource: Dict):
        """应用单个资源"""
        kind = resource.get('kind')
        name = resource.get('metadata', {}).get('name')
        
        try:
            if kind == 'ConfigMap':
                self.v1.create_namespaced_config_map(
                    namespace=self.namespace,
                    body=resource
                )
            elif kind == 'Secret':
                self.v1.create_namespaced_secret(
                    namespace=self.namespace,
                    body=resource
                )
            elif kind == 'Deployment':
                self.apps_v1.create_namespaced_deployment(
                    namespace=self.namespace,
                    body=resource
                )
            elif kind == 'Service':
                self.v1.create_namespaced_service(
                    namespace=self.namespace,
                    body=resource
                )
            elif kind == 'Ingress':
                self.networking_v1.create_namespaced_ingress(
                    namespace=self.namespace,
                    body=resource
                )
            print(f"创建 {kind} {name} 成功")
        except ApiException as e:
            if e.status == 409:
                print(f"{kind} {name} 已存在，尝试更新")
                self._update_resource(resource)
            else:
                print(f"创建 {kind} {name} 失败: {e}")
    
    def _update_resource(self, resource: Dict):
        """更新资源"""
        kind = resource.get('kind')
        name = resource.get('metadata', {}).get('name')
        
        try:
            if kind == 'ConfigMap':
                self.v1.replace_namespaced_config_map(
                    name=name,
                    namespace=self.namespace,
                    body=resource
                )
            elif kind == 'Deployment':
                self.apps_v1.replace_namespaced_deployment(
                    name=name,
                    namespace=self.namespace,
                    body=resource
                )
            elif kind == 'Service':
                self.v1.replace_namespaced_service(
                    name=name,
                    namespace=self.namespace,
                    body=resource
                )
            print(f"更新 {kind} {name} 成功")
        except ApiException as e:
            print(f"更新 {kind} {name} 失败: {e}")
    
    def get_pod_status(self) -> List[Dict]:
        """获取Pod状态"""
        try:
            pods = self.v1.list_namespaced_pod(namespace=self.namespace)
            result = []
            for pod in pods.items:
                result.append({
                    'name': pod.metadata.name,
                    'phase': pod.status.phase,
                    'ready': sum(1 for c in pod.status.container_statuses or [] if c.ready),
                    'restarts': sum(c.restart_count for c in pod.status.container_statuses or []),
                    'age': pod.metadata.creation_timestamp
                })
            return result
        except ApiException as e:
            print(f"获取Pod状态失败: {e}")
            return []
    
    def scale_deployment(self, deployment_name: str, replicas: int):
        """扩缩容部署"""
        try:
            # 获取当前部署
            deployment = self.apps_v1.read_namespaced_deployment(
                name=deployment_name,
                namespace=self.namespace
            )
            
            # 更新副本数
            deployment.spec.replicas = replicas
            
            # 应用更新
            self.apps_v1.replace_namespaced_deployment(
                name=deployment_name,
                namespace=self.namespace,
                body=deployment
            )
            print(f"部署 {deployment_name} 扩缩容到 {replicas} 个副本成功")
        except ApiException as e:
            print(f"扩缩容失败: {e}")
    
    def get_deployment_status(self) -> List[Dict]:
        """获取部署状态"""
        try:
            deployments = self.apps_v1.list_namespaced_deployment(namespace=self.namespace)
            result = []
            for deployment in deployments.items:
                result.append({
                    'name': deployment.metadata.name,
                    'ready_replicas': deployment.status.ready_replicas or 0,
                    'replicas': deployment.spec.replicas,
                    'updated_replicas': deployment.status.updated_replicas or 0,
                    'available_replicas': deployment.status.available_replicas or 0
                })
            return result
        except ApiException as e:
            print(f"获取部署状态失败: {e}")
            return []
    
    def get_service_status(self) -> List[Dict]:
        """获取服务状态"""
        try:
            services = self.v1.list_namespaced_service(namespace=self.namespace)
            result = []
            for service in services.items:
                result.append({
                    'name': service.metadata.name,
                    'type': service.spec.type,
                    'cluster_ip': service.spec.cluster_ip,
                    'external_ips': service.spec.external_i_ps or [],
                    'ports': [f"{p.port}:{p.target_port}" for p in service.spec.ports or []]
                })
            return result
        except ApiException as e:
            print(f"获取服务状态失败: {e}")
            return []
    
    def restart_deployment(self, deployment_name: str):
        """重启部署"""
        try:
            # 获取当前部署
            deployment = self.apps_v1.read_namespaced_deployment(
                name=deployment_name,
                namespace=self.namespace
            )
            
            # 添加重启注解
            if not deployment.spec.template.metadata.annotations:
                deployment.spec.template.metadata.annotations = {}
            
            from datetime import datetime
            deployment.spec.template.metadata.annotations['kubectl.kubernetes.io/restartedAt'] = \
                datetime.now().isoformat()
            
            # 应用更新
            self.apps_v1.replace_namespaced_deployment(
                name=deployment_name,
                namespace=self.namespace,
                body=deployment
            )
            print(f"重启部署 {deployment_name} 成功")
        except ApiException as e:
            print(f"重启部署失败: {e}")
    
    def get_pod_logs(self, pod_name: str, container_name: str = None) -> str:
        """获取Pod日志"""
        try:
            if container_name:
                logs = self.v1.read_namespaced_pod_log(
                    name=pod_name,
                    namespace=self.namespace,
                    container=container_name
                )
            else:
                logs = self.v1.read_namespaced_pod_log(
                    name=pod_name,
                    namespace=self.namespace
                )
            return logs
        except ApiException as e:
            print(f"获取日志失败: {e}")
            return ""
    
    def deploy_all(self):
        """部署所有资源"""
        yaml_files = [
            'k8s/namespace.yaml',
            'k8s/configmap.yaml',
            'k8s/secret.yaml',
            'k8s/storage.yaml',
            'k8s/backend-deployment.yaml',
            'k8s/frontend-deployment.yaml',
            'k8s/ingress.yaml'
        ]
        
        for yaml_file in yaml_files:
            if os.path.exists(yaml_file):
                print(f"应用 {yaml_file}")
                self.apply_yaml_file(yaml_file)
            else:
                print(f"文件 {yaml_file} 不存在")
    
    def status_report(self):
        """状态报告"""
        print("=== K8S 集群状态报告 ===")
        
        print("\n--- 部署状态 ---")
        deployments = self.get_deployment_status()
        for dep in deployments:
            print(f"{dep['name']}: {dep['ready_replicas']}/{dep['replicas']} 就绪")
        
        print("\n--- Pod 状态 ---")
        pods = self.get_pod_status()
        for pod in pods:
            print(f"{pod['name']}: {pod['phase']} (重启: {pod['restarts']})")
        
        print("\n--- 服务状态 ---")
        services = self.get_service_status()
        for svc in services:
            print(f"{svc['name']}: {svc['type']} {svc['cluster_ip']}")

# 使用示例
if __name__ == "__main__":
    k8s = K8sManager()
    
    # 部署所有资源
    k8s.deploy_all()
    
    # 查看状态
    k8s.status_report()
    
    # 扩缩容示例
    # k8s.scale_deployment('frontend-deployment', 5)
    
    # 重启部署示例
    # k8s.restart_deployment('backend-deployment')