# Stable Diffusion Multiplayer - Kubernetes 部署指南

## 📋 目录
1. [准备工作](#准备工作)
2. [环境要求](#环境要求)
3. [镜像构建](#镜像构建)
4. [配置设置](#配置设置)
5. [部署流程](#部署流程)
6. [验证测试](#验证测试)
7. [监控运维](#监控运维)
8. [故障排除](#故障排除)

---

## 🔧 准备工作

### 1. 集群要求
- **Kubernetes 版本**: >= 1.20
- **节点配置**: 普通计算节点即可（后端为 API 代理服务）
- **存储**: 支持 ReadWriteMany 的存储类
- **网络**: 支持 Ingress Controller

### 2. 必要组件
```bash
# 安装 Nginx Ingress Controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml

# 安装 Cert-Manager（SSL 证书管理）
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# 注意：无需安装 GPU Operator，后端为 API 代理服务
```

---

## 🐳 镜像构建

### 1. 构建后端镜像
```bash
# 构建后端镜像
docker build -f docker/backend.Dockerfile -t your-registry/sd-multiplayer-backend:latest .

# 推送到镜像仓库
docker push your-registry/sd-multiplayer-backend:latest
```

### 2. 构建前端镜像
```bash
# 构建前端镜像
docker build -f docker/frontend.Dockerfile -t your-registry/sd-multiplayer-frontend:latest .

# 推送到镜像仓库
docker push your-registry/sd-multiplayer-frontend:latest
```

### 3. 更新镜像引用
编辑以下文件中的镜像地址：
- `k8s/backend-deployment.yaml`
- `k8s/frontend-deployment.yaml`

将 `your-registry` 替换为实际的镜像仓库地址。

---

## ⚙️ 配置设置

### 1. 创建 Secret
```bash
# 创建 API 密钥 Secret
kubectl create secret generic sd-multiplayer-secrets \
  --from-literal=stability-api-key="sk-your-stability-api-key" \
  --from-literal=liveblocks-secret="sk_your_liveblocks_secret" \
  --namespace=stable-diffusion-multiplayer
```

### 2. 准备存储目录（本地存储）
```bash
# 在 Kubernetes 节点上创建存储目录
sudo mkdir -p /mnt/sd-multiplayer/{database,storage,models}
sudo chmod 755 /mnt/sd-multiplayer
sudo chown -R 1000:1000 /mnt/sd-multiplayer
```

### 3. 更新域名配置
编辑 `k8s/ingress.yaml`，将 `sd-multiplayer.yourdomain.com` 替换为实际域名。

---

## 🚀 部署流程

### 第一步：创建命名空间和基础配置
```bash
# 创建命名空间
kubectl apply -f k8s/namespace.yaml

# 部署配置
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
```

### 第二步：设置存储
```bash
# 部署存储配置
kubectl apply -f k8s/storage.yaml

# 验证 PVC 状态
kubectl get pvc -n stable-diffusion-multiplayer
```

### 第三步：部署应用服务
```bash
# 部署后端服务
kubectl apply -f k8s/backend-deployment.yaml

# 等待后端就绪
kubectl wait --for=condition=ready pod -l component=backend -n stable-diffusion-multiplayer --timeout=600s

# 部署前端服务
kubectl apply -f k8s/frontend-deployment.yaml

# 等待前端就绪
kubectl wait --for=condition=ready pod -l component=frontend -n stable-diffusion-multiplayer --timeout=300s
```

### 第四步：配置外部访问
```bash
# 部署 Ingress
kubectl apply -f k8s/ingress.yaml

# 获取 Ingress IP
kubectl get ingress -n stable-diffusion-multiplayer
```

---

## ✅ 验证测试

### 1. 检查 Pod 状态
```bash
# 查看所有 Pod
kubectl get pods -n stable-diffusion-multiplayer

# 查看详细状态
kubectl describe pods -n stable-diffusion-multiplayer
```

### 2. 检查服务状态
```bash
# 查看 Service
kubectl get svc -n stable-diffusion-multiplayer

# 测试内部连接
kubectl exec -it deployment/frontend-deployment -n stable-diffusion-multiplayer -- curl backend-service:7860/server/api/rooms
```

### 3. 查看日志
```bash
# 后端日志
kubectl logs -f deployment/backend-deployment -n stable-diffusion-multiplayer

# 前端日志
kubectl logs -f deployment/frontend-deployment -n stable-diffusion-multiplayer
```

### 4. 功能测试
```bash
# 端口转发测试（可选）
kubectl port-forward svc/frontend-service 8080:80 -n stable-diffusion-multiplayer

# 访问 http://localhost:8080
```

---

## 📊 监控运维

### 1. 资源监控
```bash
# 查看资源使用情况
kubectl top pods -n stable-diffusion-multiplayer
kubectl top nodes

# 查看 GPU 使用情况
kubectl describe node <gpu-node-name>
```

### 2. 扩缩容管理
```bash
# 手动扩容前端
kubectl scale deployment frontend-deployment --replicas=5 -n stable-diffusion-multiplayer

# 查看 HPA 状态
kubectl get hpa -n stable-diffusion-multiplayer
```

### 3. 更新部署
```bash
# 滚动更新
kubectl set image deployment/backend-deployment backend=your-registry/sd-multiplayer-backend:v2.0 -n stable-diffusion-multiplayer

# 查看更新状态
kubectl rollout status deployment/backend-deployment -n stable-diffusion-multiplayer

# 回滚（如需要）
kubectl rollout undo deployment/backend-deployment -n stable-diffusion-multiplayer
```

---

## 🔧 故障排除

### 常见问题

#### 1. API 连接问题
```bash
# 检查 API 密钥配置
kubectl get secret sd-multiplayer-secrets -n stable-diffusion-multiplayer -o yaml

# 测试外部 API 连接
kubectl exec -it deployment/backend-deployment -n stable-diffusion-multiplayer -- curl -s "https://api.stability.ai/v1/user/account" -H "Authorization: Bearer $STABILITY_API_KEY"
```

#### 2. 存储权限问题
```bash
# 检查存储挂载
kubectl exec -it deployment/backend-deployment -n stable-diffusion-multiplayer -- ls -la /app/stablediffusion-infinity/local_storage

# 修复权限
kubectl exec -it deployment/backend-deployment -n stable-diffusion-multiplayer -- chown -R 1000:1000 /app/stablediffusion-infinity/local_storage
```

#### 3. 网络连接问题
```bash
# 测试内部 DNS
kubectl exec -it deployment/frontend-deployment -n stable-diffusion-multiplayer -- nslookup backend-service

# 检查 Ingress
kubectl describe ingress sd-multiplayer-ingress -n stable-diffusion-multiplayer
```

#### 4. 内存不足
```bash
# 查看内存使用
kubectl top pods -n stable-diffusion-multiplayer

# 调整资源限制
kubectl patch deployment backend-deployment -n stable-diffusion-multiplayer -p '{"spec":{"template":{"spec":{"containers":[{"name":"backend","resources":{"limits":{"memory":"16Gi"}}}]}}}}'
```

### 日志调试
```bash
# 获取完整日志
kubectl logs --previous deployment/backend-deployment -n stable-diffusion-multiplayer

# 实时查看日志
kubectl logs -f deployment/backend-deployment -n stable-diffusion-multiplayer --tail=100
```

---

## 🔄 自动化部署脚本

创建一键部署脚本 `deploy.sh`：
```bash
#!/bin/bash
set -e

echo "🚀 开始部署 Stable Diffusion Multiplayer 到 Kubernetes..."

# 检查必要工具
command -v kubectl >/dev/null 2>&1 || { echo "❌ kubectl 未安装" >&2; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "❌ docker 未安装" >&2; exit 1; }

# 构建和推送镜像
echo "📦 构建 Docker 镜像..."
docker build -f docker/backend.Dockerfile -t your-registry/sd-multiplayer-backend:latest .
docker build -f docker/frontend.Dockerfile -t your-registry/sd-multiplayer-frontend:latest .

echo "⬆️ 推送镜像到仓库..."
docker push your-registry/sd-multiplayer-backend:latest
docker push your-registry/sd-multiplayer-frontend:latest

# 部署到 Kubernetes
echo "🎯 部署到 Kubernetes..."
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/storage.yaml

# 等待存储就绪
echo "⏳ 等待存储就绪..."
kubectl wait --for=condition=Bound pvc/sd-multiplayer-storage-pvc -n stable-diffusion-multiplayer --timeout=300s

# 部署服务
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/ingress.yaml

# 等待部署完成
echo "⏳ 等待服务就绪..."
kubectl wait --for=condition=ready pod -l component=backend -n stable-diffusion-multiplayer --timeout=600s
kubectl wait --for=condition=ready pod -l component=frontend -n stable-diffusion-multiplayer --timeout=300s

echo "✅ 部署完成！"
echo "🌐 访问地址: https://sd-multiplayer.yourdomain.com"
echo "📊 查看状态: kubectl get pods -n stable-diffusion-multiplayer"
```

---

## 📚 相关资源

- [Kubernetes 官方文档](https://kubernetes.io/docs/)
- [NVIDIA GPU Operator](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/overview.html)
- [Nginx Ingress Controller](https://kubernetes.github.io/ingress-nginx/)
- [Cert-Manager 文档](https://cert-manager.io/docs/)

---

## 🆘 技术支持

如遇到问题，请检查：
1. 集群资源是否充足
2. API 密钥是否正确配置
3. 网络策略是否允许通信
4. 存储配置是否正确
5. 外部 API 服务是否可访问

通过以上指南，您应该能够成功将 Stable Diffusion Multiplayer 部署到 Kubernetes 集群中。 