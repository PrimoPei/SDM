#!/bin/bash
set -e

echo "🚀 开始部署 Stable Diffusion Multiplayer 到 Kubernetes..."

# 检查必要工具
command -v kubectl >/dev/null 2>&1 || { echo "❌ kubectl 未安装" >&2; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "❌ docker 未安装" >&2; exit 1; }

# 检查环境变量
if [ -z "$STABILITY_API_KEY" ] || [ -z "$LIVEBLOCKS_SECRET" ]; then
    echo "❌ 请设置环境变量："
    echo "   export STABILITY_API_KEY='your-stability-api-key'"
    echo "   export LIVEBLOCKS_SECRET='your-liveblocks-secret'"
    exit 1
fi

# 设置镜像仓库（请修改为您的仓库地址）
REGISTRY="your-registry"
if [ "$REGISTRY" = "your-registry" ]; then
    echo "❌ 请在脚本中设置正确的镜像仓库地址"
    exit 1
fi

# 构建和推送镜像
echo "📦 构建 Docker 镜像..."
docker build -f docker/backend.Dockerfile -t $REGISTRY/sd-multiplayer-backend:latest .
docker build -f docker/frontend.Dockerfile -t $REGISTRY/sd-multiplayer-frontend:latest .

echo "⬆️ 推送镜像到仓库..."
docker push $REGISTRY/sd-multiplayer-backend:latest
docker push $REGISTRY/sd-multiplayer-frontend:latest

# 创建命名空间
echo "🎯 创建 Kubernetes 命名空间..."
kubectl apply -f k8s/namespace.yaml

# 创建 Secret
echo "🔐 创建 API 密钥..."
kubectl create secret generic sd-multiplayer-secrets \
  --from-literal=stability-api-key="$STABILITY_API_KEY" \
  --from-literal=liveblocks-secret="$LIVEBLOCKS_SECRET" \
  --namespace=stable-diffusion-multiplayer \
  --dry-run=client -o yaml | kubectl apply -f -

# 部署配置
echo "⚙️ 部署配置..."
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/storage.yaml

# 等待存储就绪
echo "⏳ 等待存储就绪..."
kubectl wait --for=condition=Bound pvc/sd-multiplayer-storage-pvc -n stable-diffusion-multiplayer --timeout=300s
kubectl wait --for=condition=Bound pvc/sd-multiplayer-db-pvc -n stable-diffusion-multiplayer --timeout=300s

# 部署服务
echo "🚀 部署应用服务..."
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml

# 等待部署完成
echo "⏳ 等待服务就绪..."
kubectl wait --for=condition=ready pod -l component=backend -n stable-diffusion-multiplayer --timeout=300s
kubectl wait --for=condition=ready pod -l component=frontend -n stable-diffusion-multiplayer --timeout=300s

# 部署 Ingress
echo "🌐 配置外部访问..."
kubectl apply -f k8s/ingress.yaml

echo "✅ 部署完成！"
echo ""
echo "📊 查看状态:"
echo "   kubectl get pods -n stable-diffusion-multiplayer"
echo ""
echo "🌐 访问方式:"
echo "   1. 通过 Ingress: https://sd-multiplayer.yourdomain.com"
echo "   2. 通过端口转发: kubectl port-forward svc/frontend-service 8080:80 -n stable-diffusion-multiplayer"
echo ""
echo "📝 查看日志:"
echo "   kubectl logs -f deployment/backend-deployment -n stable-diffusion-multiplayer"
echo "   kubectl logs -f deployment/frontend-deployment -n stable-diffusion-multiplayer" 