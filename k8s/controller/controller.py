# controller/sd_controller.py
import asyncio
import logging
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException
import re

import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SDMultiplayerController:
    def __init__(self, namespace: str = "stable-diffusion-multiplayer"):
        """初始化 SD Multiplayer Controller"""
        try:
            config.load_incluster_config()
        except:
            config.load_kube_config()
        
        self.namespace = namespace
        self.v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        self.networking_v1 = client.NetworkingV1Api()
        self.custom_api = client.CustomObjectsApi()
        
        # CRD 信息
        self.group = "ai.example.com"
        self.version = "v1"
        self.plural = "sdmultiplayers"
        
        # 资源模板
        self.resource_templates = self._load_resource_templates()
        
        # 任务队列管理
        self.task_queue = asyncio.Queue()
        self.active_tasks = {}
        
    def _load_resource_templates(self) -> Dict[str, Any]:
        """加载资源模板"""
        templates = {}
        
        # Frontend Deployment 模板
        templates['frontend_deployment'] = {
            'apiVersion': 'apps/v1',
            'kind': 'Deployment',
            'metadata': {
                'name': 'frontend-deployment',
                'namespace': self.namespace,
                'labels': {
                    'app': 'sd-multiplayer',
                    'component': 'frontend',
                    'managed-by': 'sd-controller'
                }
            },
            'spec': {
                'selector': {
                    'matchLabels': {
                        'app': 'sd-multiplayer',
                        'component': 'frontend'
                    }
                },
                'template': {
                    'metadata': {
                        'labels': {
                            'app': 'sd-multiplayer',
                            'component': 'frontend'
                        }
                    },
                    'spec': {
                        'containers': [{
                            'name': 'frontend',
                            'ports': [{'containerPort': 80, 'name': 'http'}],
                            'livenessProbe': {
                                'httpGet': {'path': '/', 'port': 80},
                                'initialDelaySeconds': 30,
                                'periodSeconds': 30
                            },
                            'readinessProbe': {
                                'httpGet': {'path': '/', 'port': 80},
                                'initialDelaySeconds': 5,
                                'periodSeconds': 10
                            }
                        }]
                    }
                }
            }
        }
        
        # Backend Deployment 模板
        templates['backend_deployment'] = {
            'apiVersion': 'apps/v1',
            'kind': 'Deployment',
            'metadata': {
                'name': 'backend-deployment',
                'namespace': self.namespace,
                'labels': {
                    'app': 'sd-multiplayer',
                    'component': 'backend',
                    'managed-by': 'sd-controller'
                }
            },
            'spec': {
                'selector': {
                    'matchLabels': {
                        'app': 'sd-multiplayer',
                        'component': 'backend'
                    }
                },
                'template': {
                    'metadata': {
                        'labels': {
                            'app': 'sd-multiplayer',
                            'component': 'backend'
                        }
                    },
                    'spec': {
                        'containers': [{
                            'name': 'backend',
                            'ports': [{'containerPort': 7860, 'name': 'http'}],
                            'livenessProbe': {
                                'httpGet': {'path': '/server/api/health', 'port': 7860},
                                'initialDelaySeconds': 60,
                                'periodSeconds': 30
                            },
                            'readinessProbe': {
                                'httpGet': {'path': '/server/api/health', 'port': 7860},
                                'initialDelaySeconds': 30,
                                'periodSeconds': 10
                            }
                        }]
                    }
                }
            }
        }
        
        # Service 模板
        templates['frontend_service'] = {
            'apiVersion': 'v1',
            'kind': 'Service',
            'metadata': {
                'name': 'frontend-service',
                'namespace': self.namespace,
                'labels': {
                    'app': 'sd-multiplayer',
                    'component': 'frontend',
                    'managed-by': 'sd-controller'
                }
            },
            'spec': {
                'type': 'ClusterIP',
                'ports': [{'port': 80, 'targetPort': 80, 'name': 'http'}],
                'selector': {
                    'app': 'sd-multiplayer',
                    'component': 'frontend'
                }
            }
        }
        
        templates['backend_service'] = {
            'apiVersion': 'v1',
            'kind': 'Service',
            'metadata': {
                'name': 'backend-service',
                'namespace': self.namespace,
                'labels': {
                    'app': 'sd-multiplayer',
                    'component': 'backend',
                    'managed-by': 'sd-controller'
                }
            },
            'spec': {
                'type': 'ClusterIP',
                'ports': [{'port': 7860, 'targetPort': 7860, 'name': 'http'}],
                'selector': {
                    'app': 'sd-multiplayer',
                    'component': 'backend'
                }
            }
        }
        
        return templates
    
    async def watch_custom_resources(self):
        """监听自定义资源变化"""
        logger.info(f"开始监听 {self.plural} 资源变化")
        
        while True:
            try:
                w = watch.Watch()
                for event in w.stream(
                    self.custom_api.list_namespaced_custom_object,
                    group=self.group,
                    version=self.version,
                    namespace=self.namespace,
                    plural=self.plural,
                    timeout_seconds=600
                ):
                    event_type = event['type']
                    sd_resource = event['object']
                    
                    logger.info(f"收到事件: {event_type} - {sd_resource['metadata']['name']}")
                    
                    if event_type in ['ADDED', 'MODIFIED']:
                        await self._handle_resource_change(sd_resource)
                    elif event_type == 'DELETED':
                        await self._handle_resource_deletion(sd_resource)
                        
            except Exception as e:
                logger.error(f"监听资源变化时发生错误: {e}")
                await asyncio.sleep(10)
    
    async def _handle_resource_change(self, sd_resource: Dict[str, Any]):
        """处理资源变化"""
        name = sd_resource['metadata']['name']
        spec = sd_resource.get('spec', {})
        
        try:
            # 更新状态为 Pending
            await self._update_status(name, 'Pending', '开始处理资源变化')
            
            # 创建或更新 ConfigMap
            await self._ensure_configmap(name, spec)
            
            # 创建或更新 Secret
            await self._ensure_secret(name, spec)
            
            # 创建或更新 Storage
            await self._ensure_storage(name, spec)
            
            # 创建或更新 Frontend
            await self._ensure_frontend(name, spec)
            
            # 创建或更新 Backend
            await self._ensure_backend(name, spec)
            
            # 创建或更新 Service
            await self._ensure_services(name, spec)
            
            # 创建或更新 Ingress
            await self._ensure_ingress(name, spec)
            
            # 启动任务队列监控
            await self._start_task_monitoring(name)
            
            # 更新状态为 Running
            await self._update_status(name, 'Running', '所有组件已成功部署')
            
        except Exception as e:
            logger.error(f"处理资源 {name} 时发生错误: {e}")
            await self._update_status(name, 'Failed', f'部署失败: {str(e)}')
    
    async def _handle_resource_deletion(self, sd_resource: Dict[str, Any]):
        """处理资源删除"""
        name = sd_resource['metadata']['name']
        
        try:
            # 删除所有相关资源
            await self._cleanup_resources(name)
            logger.info(f"已清理资源 {name}")
            
        except Exception as e:
            logger.error(f"清理资源 {name} 时发生错误: {e}")
    
    async def _ensure_configmap(self, name: str, spec: Dict[str, Any]):
        """确保 ConfigMap 存在"""
        config_data = {
            'APP_ENV': 'production',
            'LOG_LEVEL': spec.get('config', {}).get('logLevel', 'info'),
            'BACKEND_HOST': '0.0.0.0',
            'BACKEND_PORT': '7860',
            'MAX_CONCURRENT_TASKS': str(spec.get('config', {}).get('maxConcurrentTasks', 10)),
            'NGINX_WORKER_PROCESSES': 'auto'
        }
        
        configmap = {
            'apiVersion': 'v1',
            'kind': 'ConfigMap',
            'metadata': {
                'name': f'{name}-config',
                'namespace': self.namespace,
                'labels': {
                    'app': 'sd-multiplayer',
                    'instance': name,
                    'managed-by': 'sd-controller'
                }
            },
            'data': config_data
        }
        
        try:
            self.v1.create_namespaced_config_map(
                namespace=self.namespace,
                body=configmap
            )
            logger.info(f"创建 ConfigMap {name}-config")
        except ApiException as e:
            if e.status == 409:
                self.v1.replace_namespaced_config_map(
                    name=f'{name}-config',
                    namespace=self.namespace,
                    body=configmap
                )
                logger.info(f"更新 ConfigMap {name}-config")
            else:
                raise
    
    async def _ensure_secret(self, name: str, spec: Dict[str, Any]):
        """确保 Secret 存在"""
        import base64
        
        api_keys = spec.get('config', {}).get('apiKeys', {})
        secret_data = {}
        
        if api_keys.get('stabilityApiKey'):
            secret_data['stability-api-key'] = base64.b64encode(
                api_keys['stabilityApiKey'].encode()
            ).decode()
        
        if api_keys.get('liveblocksSecret'):
            secret_data['liveblocks-secret'] = base64.b64encode(
                api_keys['liveblocksSecret'].encode()
            ).decode()
        
        if not secret_data:
            return
        
        secret = {
            'apiVersion': 'v1',
            'kind': 'Secret',
            'metadata': {
                'name': f'{name}-secrets',
                'namespace': self.namespace,
                'labels': {
                    'app': 'sd-multiplayer',
                    'instance': name,
                    'managed-by': 'sd-controller'
                }
            },
            'type': 'Opaque',
            'data': secret_data
        }
        
        try:
            self.v1.create_namespaced_secret(
                namespace=self.namespace,
                body=secret
            )
            logger.info(f"创建 Secret {name}-secrets")
        except ApiException as e:
            if e.status == 409:
                self.v1.replace_namespaced_secret(
                    name=f'{name}-secrets',
                    namespace=self.namespace,
                    body=secret
                )
                logger.info(f"更新 Secret {name}-secrets")
            else:
                raise
    
    async def _ensure_storage(self, name: str, spec: Dict[str, Any]):
        """确保存储资源存在"""
        storage_spec = spec.get('storage', {})
        storage_size = storage_spec.get('size', '10Gi')
        storage_class = storage_spec.get('storageClass', 'standard')
        
        # 创建 PVC
        pvc = {
            'apiVersion': 'v1',
            'kind': 'PersistentVolumeClaim',
            'metadata': {
                'name': f'{name}-storage-pvc',
                'namespace': self.namespace,
                'labels': {
                    'app': 'sd-multiplayer',
                    'instance': name,
                    'managed-by': 'sd-controller'
                }
            },
            'spec': {
                'accessModes': ['ReadWriteOnce'],
                'resources': {
                    'requests': {'storage': storage_size}
                },
                'storageClassName': storage_class
            }
        }
        
        try:
            self.v1.create_namespaced_persistent_volume_claim(
                namespace=self.namespace,
                body=pvc
            )
            logger.info(f"创建 PVC {name}-storage-pvc")
        except ApiException as e:
            if e.status == 409:
                logger.info(f"PVC {name}-storage-pvc 已存在")
            else:
                raise
    
    async def _ensure_frontend(self, name: str, spec: Dict[str, Any]):
        """确保前端部署存在"""
        frontend_spec = spec.get('frontend', {})
        
        deployment = self.resource_templates['frontend_deployment'].copy()
        deployment['metadata']['name'] = f'{name}-frontend'
        deployment['metadata']['labels']['instance'] = name
        deployment['spec']['replicas'] = frontend_spec.get('replicas', 3)
        
        deployment['spec']['template']['metadata']['labels']['instance'] = name
        # 更新容器配置
        container = deployment['spec']['template']['spec']['containers'][0]
        container['image'] = frontend_spec.get('image', 'primay73/sd-multiplayer-frontend:test')
        
        if 'resources' in frontend_spec:
            container['resources'] = frontend_spec['resources']
        
        # 添加环境变量
        container['env'] = [
            {
                'name': 'NGINX_WORKER_PROCESSES',
                'valueFrom': {
                    'configMapKeyRef': {
                        'name': f'{name}-config',
                        'key': 'NGINX_WORKER_PROCESSES'
                    }
                }
            }
        ]
        
        try:
            self.apps_v1.create_namespaced_deployment(
                namespace=self.namespace,
                body=deployment
            )
            logger.info(f"创建前端部署 {name}-frontend")
        except ApiException as e:
            if e.status == 409:
                self.apps_v1.replace_namespaced_deployment(
                    name=f'{name}-frontend',
                    namespace=self.namespace,
                    body=deployment
                )
                logger.info(f"更新前端部署 {name}-frontend")
            else:
                raise
    
    async def _ensure_backend(self, name: str, spec: Dict[str, Any]):
        """确保后端部署存在"""
        backend_spec = spec.get('backend', {})
        
        deployment = self.resource_templates['backend_deployment'].copy()
        deployment['metadata']['name'] = f'{name}-backend'
        deployment['metadata']['labels']['instance'] = name
        deployment['spec']['replicas'] = backend_spec.get('replicas', 1)
        
        deployment['spec']['template']['metadata']['labels']['instance'] = name
        # 更新容器配置
        container = deployment['spec']['template']['spec']['containers'][0]
        container['image'] = backend_spec.get('image', 'primay73/sd-multiplayer-backend:test')
        
        if 'resources' in backend_spec:
            container['resources'] = backend_spec['resources']
        
        # 添加环境变量
        container['env'] = [
            {
                'name': 'LOG_LEVEL',
                'valueFrom': {
                    'configMapKeyRef': {
                        'name': f'{name}-config',
                        'key': 'LOG_LEVEL'
                    }
                }
            },
            {
                'name': 'STABILITY_API_KEY',
                'valueFrom': {
                    'secretKeyRef': {
                        'name': f'{name}-secrets',
                        'key': 'stability-api-key'
                    }
                }
            }
        ]
        
        # 添加存储挂载
        container['volumeMounts'] = [
            {
                'name': 'storage-volume',
                'mountPath': '/app/stablediffusion-infinity/local_storage'
            }
        ]
        
        deployment['spec']['template']['spec']['volumes'] = [
            {
                'name': 'storage-volume',
                'persistentVolumeClaim': {
                    'claimName': f'{name}-storage-pvc'
                }
            }
        ]
        
        # GPU 配置
        if backend_spec.get('gpuRequired', False):
            container['resources'] = container.get('resources', {})
            container['resources']['limits'] = container['resources'].get('limits', {})
            container['resources']['limits']['nvidia.com/gpu'] = '1'
        
        try:
            self.apps_v1.create_namespaced_deployment(
                namespace=self.namespace,
                body=deployment
            )
            logger.info(f"创建后端部署 {name}-backend")
        except ApiException as e:
            if e.status == 409:
                self.apps_v1.replace_namespaced_deployment(
                    name=f'{name}-backend',
                    namespace=self.namespace,
                    body=deployment
                )
                logger.info(f"更新后端部署 {name}-backend")
            else:
                raise
    
    async def _ensure_services(self, name: str, spec: Dict[str, Any]):
        """确保服务存在"""
        # 前端服务
        frontend_service = self.resource_templates['frontend_service'].copy()
        frontend_service['metadata']['name'] = f'{name}-frontend-service'
        frontend_service['metadata']['labels']['instance'] = name
        frontend_service['spec']['selector']['instance'] = name
        
        # 后端服务
        backend_service = self.resource_templates['backend_service'].copy()
        backend_service['metadata']['name'] = f'{name}-backend-service'
        backend_service['metadata']['labels']['instance'] = name
        backend_service['spec']['selector']['instance'] = name
        
        for service in [frontend_service, backend_service]:
            try:
                self.v1.create_namespaced_service(
                    namespace=self.namespace,
                    body=service
                )
                logger.info(f"创建服务 {service['metadata']['name']}")
            except ApiException as e:
                if e.status == 409:
                    self.v1.replace_namespaced_service(
                        name=service['metadata']['name'],
                        namespace=self.namespace,
                        body=service
                    )
                    logger.info(f"更新服务 {service['metadata']['name']}")
                else:
                    raise
    
    async def _ensure_ingress(self, name: str, spec: Dict[str, Any]):
        """确保 Ingress 存在"""
        ingress = {
            'apiVersion': 'networking.k8s.io/v1',
            'kind': 'Ingress',
            'metadata': {
                'name': f'{name}-ingress',
                'namespace': self.namespace,
                'labels': {
                    'app': 'sd-multiplayer',
                    'instance': name,
                    'managed-by': 'sd-controller'
                },
                'annotations': {
                    'kubernetes.io/ingress.class': 'nginx',
                    'nginx.ingress.kubernetes.io/proxy-body-size': '100m'
                }
            },
            'spec': {
                'rules': [
                    {
                        'host': f'{name}.sd-multiplayer.local',
                        'http': {
                            'paths': [
                                {
                                    'path': '/',
                                    'pathType': 'Prefix',
                                    'backend': {
                                        'service': {
                                            'name': f'{name}-frontend-service',
                                            'port': {'number': 80}
                                        }
                                    }
                                },
                                {
                                    'path': '/server',
                                    'pathType': 'Prefix',
                                    'backend': {
                                        'service': {
                                            'name': f'{name}-backend-service',
                                            'port': {'number': 7860}
                                        }
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        }
        
        try:
            self.networking_v1.create_namespaced_ingress(
                namespace=self.namespace,
                body=ingress
            )
            logger.info(f"创建 Ingress {name}-ingress")
        except ApiException as e:
            if e.status == 409:
                self.networking_v1.replace_namespaced_ingress(
                    name=f'{name}-ingress',
                    namespace=self.namespace,
                    body=ingress
                )
                logger.info(f"更新 Ingress {name}-ingress")
            else:
                raise
    
    async def _start_task_monitoring(self, name: str):
        """启动任务队列监控"""
        if name not in self.active_tasks:
            self.active_tasks[name] = {
                'total_jobs': 0,
                'active_jobs': 0,
                'last_scale_time': datetime.now(timezone.utc)
            }
        
        # 启动负载监控任务
        asyncio.create_task(self._monitor_load(name))
    
    async def _monitor_load(self, name: str):
        """监控负载并自动扩缩容"""
        while True:
            try:
                # 获取当前负载
                load_metrics = await self._get_load_metrics(name)
                
                # 根据负载决定是否扩缩容
                if load_metrics['cpu_usage'] > 80:
                    await self._scale_backend(name, 'up')
                elif load_metrics['cpu_usage'] < 20:
                    await self._scale_backend(name, 'down')
                
                # 更新任务统计
                self.active_tasks[name]['active_jobs'] = load_metrics['active_jobs']
                
                # 更新资源状态
                await self._update_resource_status(name)
                
            except Exception as e:
                logger.error(f"监控负载时发生错误: {e}")
            
            await asyncio.sleep(30)  # 每30秒检查一次
    

    async def _get_backend_resource_requests(self, name: str) -> Dict[str, int]:
        """获取后端 Deployment 资源请求的总量 (milliCPU 和 MiB)"""
        try:
            deployment = self.apps_v1.read_namespaced_deployment(
                name=f'{name}-backend',
                namespace=self.namespace
            )
            
            total_requests = {'cpu': 0, 'memory': 0}
            
            # 获取单个 pod 的资源请求
            container_requests = deployment.spec.template.spec.containers[0].resources.requests
            if not container_requests:
                return total_requests

            # 解析 CPU (e.g., "500m" -> 500, "1" -> 1000)
            cpu_request_str = container_requests.get('cpu', '0')
            if 'm' in cpu_request_str:
                total_requests['cpu'] = int(cpu_request_str.replace('m', ''))
            else:
                total_requests['cpu'] = int(cpu_request_str) * 1000

            # 解析内存 (e.g., "2Gi" -> 2048, "512Mi" -> 512)
            mem_request_str = container_requests.get('memory', '0')
            mem_value = int(re.search(r'\d+', mem_request_str).group())
            if 'Gi' in mem_request_str:
                total_requests['memory'] = mem_value * 1024
            elif 'Mi' in mem_request_str:
                total_requests['memory'] = mem_value
            elif 'Ki' in mem_request_str:
                total_requests['memory'] = mem_value / 1024
            
            # 乘以副本数得到总量
            replicas = deployment.spec.replicas
            total_requests['cpu'] *= replicas
            total_requests['memory'] *= replicas
            
            return total_requests

        except ApiException as e:
            if e.status == 404:
                logger.warning(f"获取后端部署 {name}-backend 的资源请求时未找到该部署")
                return {'cpu': 0, 'memory': 0}
            else:
                logger.error(f"获取后端部署 {name}-backend 的资源请求时出错: {e}")
                raise

    async def _get_load_metrics(self, name: str) -> Dict[str, Any]:
        """
        从 Kubernetes Metrics Server 获取 CPU/内存负载指标.
        TODO: 从 Prometheus 获取自定义指标.
        """
        logger.info(f"正在为实例 {name} 获取负载指标...")
        
        # 定义后端 pod 的标签选择器
        label_selector = f"app=sd-multiplayer,component=backend,instance={name}"
        
        # 初始化返回值
        metrics = {
            'cpu_usage_percent': 0,
            'memory_usage_percent': 0,
            'active_jobs': 0, # TODO: 从 Prometheus 获取
            'queue_length': 0  # TODO: 从 Prometheus 获取
        }

        # --- 1. 从 Metrics Server 获取 CPU 和内存使用情况 ---
        try:
            # 查询与此实例后端匹配的所有 Pod 的指标
            pod_metrics = self.custom_api.list_namespaced_custom_object(
                group="metrics.k8s.io",
                version="v1beta1",
                namespace=self.namespace,
                plural="pods",
                label_selector=label_selector
            )

            if not pod_metrics['items']:
                logger.warning(f"未找到实例 {name} 的 Pod 指标，可能 Metrics Server 未就绪或 Pod 正在启动")
                return metrics

            total_cpu_usage = 0  # in nanocores
            total_memory_usage = 0 # in KiB

            for item in pod_metrics['items']:
                for container in item['containers']:
                    # CPU 使用量，单位是 n (纳核心)
                    cpu_usage_str = container.get('usage', {}).get('cpu', '0n')
                    total_cpu_usage += int(cpu_usage_str.replace('n', ''))
                    
                    # 内存使用量，单位是 Ki (Kibibytes)
                    mem_usage_str = container.get('usage', {}).get('memory', '0Ki')
                    total_memory_usage += int(mem_usage_str.replace('Ki', ''))

            # 获取后端 Deployment 请求的总资源量
            total_requests = await self._get_backend_resource_requests(name)
            
            # 计算使用率百分比
            if total_requests['cpu'] > 0:
                # 将请求的 milliCPU 转换为 nanoCPU
                total_cpu_request_nano = total_requests['cpu'] * 1_000_000
                metrics['cpu_usage_percent'] = (total_cpu_usage / total_cpu_request_nano) * 100
            
            if total_requests['memory'] > 0:
                # 将请求的 MiB 转换为 KiB
                total_mem_request_kib = total_requests['memory'] * 1024
                metrics['memory_usage_percent'] = (total_memory_usage / total_mem_request_kib) * 100
            
            logger.info(f"实例 {name} 的资源使用率: CPU={metrics['cpu_usage_percent']:.2f}%, Memory={metrics['memory_usage_percent']:.2f}%")

        except ApiException as e:
            logger.error(f"从 Metrics Server 获取 Pod 指标失败: {e}. 请确保 Metrics Server 已在集群中安装并运行。")
        except Exception as e:
            logger.error(f"处理指标数据时发生未知错误: {e}")

        # --- 2. TODO: 从 Prometheus 获取自定义指标 ---
        # 以下是示例逻辑，您需要替换为对 Prometheus 的真实查询
        try:
            # 假设您的应用暴露了名为 `sd_active_jobs` 和 `sd_queue_length` 的指标
            # metrics['active_jobs'] = await self._query_prometheus("sum(sd_active_jobs{instance='" + name + "'})")
            # metrics['queue_length'] = await self._query_prometheus("sum(sd_queue_length{instance='" + name + "'})")
            
            # 在您实现 Prometheus 查询前，我们暂时返回一个模拟值
            import random
            metrics['active_jobs'] = random.randint(1, 10)
            metrics['queue_length'] = random.randint(0, 20)
            logger.info(f"实例 {name} 的自定义指标 (模拟): ActiveJobs={metrics['active_jobs']}, QueueLength={metrics['queue_length']}")

        except Exception as e:
            logger.error(f"从 Prometheus 获取自定义指标时出错: {e}")

        return metrics

# 别忘了修改 _monitor_load 函数以使用新的返回值
    async def _monitor_load(self, name: str):
        """监控负载并自动扩缩容"""
        while True:
            try:
                # 获取当前负载
                load_metrics = await self._get_load_metrics(name)
                
                # 根据负载决定是否扩缩容 (现在使用 cpu_usage_percent)
                if load_metrics['cpu_usage_percent'] > 80:
                    await self._scale_backend(name, 'up')
                elif load_metrics['cpu_usage_percent'] < 20:
                    await self._scale_backend(name, 'down')
                
                # 更新任务统计
                self.active_tasks[name]['active_jobs'] = load_metrics['active_jobs']
                
                # 更新资源状态
                await self._update_resource_status(name)
                
            except Exception as e:
                logger.error(f"监控负载时发生错误: {e}")
            
            await asyncio.sleep(30)  # 每30秒检查一次
    
    async def _scale_backend(self, name: str, direction: str):
        """扩缩容后端服务"""
        try:
            deployment = self.apps_v1.read_namespaced_deployment(
                name=f'{name}-backend',
                namespace=self.namespace
            )
            
            current_replicas = deployment.spec.replicas
            
            if direction == 'up' and current_replicas < 5:
                new_replicas = current_replicas + 1
            elif direction == 'down' and current_replicas > 1:
                new_replicas = current_replicas - 1
            else:
                return
            
            deployment.spec.replicas = new_replicas
            
            self.apps_v1.replace_namespaced_deployment(
                name=f'{name}-backend',
                namespace=self.namespace,
                body=deployment
            )
            
            logger.info(f"扩缩容后端服务 {name} 到 {new_replicas} 个副本")
            
        except Exception as e:
            logger.error(f"扩缩容失败: {e}")
    
    async def _update_status(self, name: str, phase: str, message: str):
        """更新自定义资源状态"""
        try:
            # 获取当前资源
            resource = self.custom_api.get_namespaced_custom_object(
                group=self.group,
                version=self.version,
                namespace=self.namespace,
                plural=self.plural,
                name=name
            )
            
            # 更新状态
            if 'status' not in resource:
                resource['status'] = {}
            
            resource['status']['phase'] = phase
            resource['status']['lastUpdateTime'] = datetime.now(timezone.utc).isoformat()
            
            # 更新条件
            condition = {
                'type': 'Ready',
                'status': 'True' if phase == 'Running' else 'False',
                'lastTransitionTime': datetime.now(timezone.utc).isoformat(),
                'reason': phase,
                'message': message
            }
            
            if 'conditions' not in resource['status']:
                resource['status']['conditions'] = []
            
            resource['status']['conditions'].append(condition)
            
            # 保持最近的 5 个条件
            resource['status']['conditions'] = resource['status']['conditions'][-5:]
            
            # 更新资源
            self.custom_api.replace_namespaced_custom_object_status(
                group=self.group,
                version=self.version,
                namespace=self.namespace,
                plural=self.plural,
                name=name,
                body=resource
            )
            
            logger.info(f"更新资源 {name} 状态: {phase}")
            
        except Exception as e:
            logger.error(f"更新状态失败: {e}")
    
    async def _update_resource_status(self, name: str):
        """更新资源运行状态"""
        try:
            # 获取部署状态
            frontend_deployment = self.apps_v1.read_namespaced_deployment(
                name=f'{name}-frontend',
                namespace=self.namespace
            )
            
            backend_deployment = self.apps_v1.read_namespaced_deployment(
                name=f'{name}-backend',
                namespace=self.namespace
            )
            
            # 获取当前资源
            resource = self.custom_api.get_namespaced_custom_object(
                group=self.group,
                version=self.version,
                namespace=self.namespace,
                plural=self.plural,
                name=name
            )
            
            # 更新状态
            if 'status' not in resource:
                resource['status'] = {}
            
            resource['status']['frontendReplicas'] = frontend_deployment.status.ready_replicas or 0
            resource['status']['backendReplicas'] = backend_deployment.status.ready_replicas or 0
            resource['status']['activeJobs'] = self.active_tasks[name]['active_jobs']
            resource['status']['totalJobs'] = self.active_tasks[name]['total_jobs']
            
            # 更新资源
            self.custom_api.replace_namespaced_custom_object_status(
                group=self.group,
                version=self.version,
                namespace=self.namespace,
                plural=self.plural,
                name=name,
                body=resource
            )
            
        except Exception as e:
            logger.error(f"更新资源状态失败: {e}")
    
    async def _cleanup_resources(self, name: str):
        """清理资源"""
        resources_to_delete = [
            ('apps/v1', 'deployments', f'{name}-frontend'),
            ('apps/v1', 'deployments', f'{name}-backend'),
            ('v1', 'services', f'{name}-frontend-service'),
            ('v1', 'services', f'{name}-backend-service'),
            ('networking.k8s.io/v1', 'ingresses', f'{name}-ingress'),
            ('v1', 'configmaps', f'{name}-config'),
            ('v1', 'secrets', f'{name}-secrets'),
            ('v1', 'persistentvolumeclaims', f'{name}-storage-pvc')
        ]
        
        for api_version, kind, resource_name in resources_to_delete:
            try:
                if api_version == 'apps/v1' and kind == 'deployments':
                    self.apps_v1.delete_namespaced_deployment(
                        name=resource_name,
                        namespace=self.namespace
                    )
                elif api_version == 'v1' and kind == 'services':
                    self.v1.delete_namespaced_service(
                        name=resource_name,
                        namespace=self.namespace
                    )
                elif api_version == 'networking.k8s.io/v1' and kind == 'ingresses':
                    self.networking_v1.delete_namespaced_ingress(
                        name=resource_name,
                        namespace=self.namespace
                    )
                elif api_version == 'v1' and kind == 'configmaps':
                    self.v1.delete_namespaced_config_map(
                        name=resource_name,
                        namespace=self.namespace
                    )
                elif api_version == 'v1' and kind == 'secrets':
                    self.v1.delete_namespaced_secret(
                        name=resource_name,
                        namespace=self.namespace
                    )
                elif api_version == 'v1' and kind == 'persistentvolumeclaims':
                    self.v1.delete_namespaced_persistent_volume_claim(
                        name=resource_name,
                        namespace=self.namespace
                    )
                
                logger.info(f"删除资源 {resource_name}")
                
            except ApiException as e:
                if e.status == 404:
                    logger.info(f"资源 {resource_name} 不存在")
                else:
                    logger.error(f"删除资源 {resource_name} 失败: {e}")
    
    async def run(self):
        """运行 Controller"""
        logger.info("启动 SD Multiplayer Controller")
        
               
        # 启动监听任务
        await self.watch_custom_resources()

# 启动 Controller
async def main():
    controller = SDMultiplayerController()
    await controller.run()

if __name__ == "__main__":
    asyncio.run(main())