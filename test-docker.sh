#!/bin/bash
set -e

echo "🐳 开始测试 Docker 镜像..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查环境变量
check_env() {
    echo "🔍 检查环境变量..."
    if [ -z "$STABILITY_API_KEY" ]; then
        echo -e "${YELLOW}警告: STABILITY_API_KEY 未设置${NC}"
        echo "请执行: export STABILITY_API_KEY='your-api-key'"
    else
        echo -e "${GREEN}✓ STABILITY_API_KEY 已设置${NC}"
    fi
    
    if [ -z "$LIVEBLOCKS_SECRET" ]; then
        echo -e "${YELLOW}警告: LIVEBLOCKS_SECRET 未设置${NC}"
        echo "请执行: export LIVEBLOCKS_SECRET='your-secret'"
    else
        echo -e "${GREEN}✓ LIVEBLOCKS_SECRET 已设置${NC}"
    fi
}

# 清理函数
cleanup() {
    echo "🧹 清理测试环境..."
    docker stop backend-service 2>/dev/null || true
    docker stop sd-frontend-test 2>/dev/null || true
    docker rm backend-service 2>/dev/null || true
    docker rm sd-frontend-test 2>/dev/null || true
    docker network rm sd-test-network 2>/dev/null || true
    rm -rf ./test-data 2>/dev/null || true
}

# 构建镜像
build_images() {
    echo "📦 构建 Docker 镜像..."
    
    # 检查必要文件是否存在
    if [ ! -f "requirements.txt" ]; then
        echo -e "${RED}❌ requirements.txt 文件不存在${NC}"
        echo "请确保在项目根目录执行此脚本"
        exit 1
    fi
    
    if [ ! -f "docker/backend.Dockerfile" ]; then
        echo -e "${RED}❌ docker/backend.Dockerfile 文件不存在${NC}"
        exit 1
    fi
    
    if [ ! -f "docker/frontend.Dockerfile" ]; then
        echo -e "${RED}❌ docker/frontend.Dockerfile 文件不存在${NC}"
        exit 1
    fi
    
    # 设置使用传统构建器，避免 buildx 问题
    export DOCKER_BUILDKIT=0
    
    echo "构建后端镜像..."
    docker build --no-cache -f docker/backend.Dockerfile -t sd-multiplayer-backend:test . || {
        echo -e "${RED}❌ 后端镜像构建失败${NC}"
        echo "请检查 Dockerfile 和构建上下文"
        echo "如果是 buildx 问题，请参考解决方案"
        exit 1
    }
    echo -e "${GREEN}✓ 后端镜像构建成功${NC}"
    
    echo "构建前端镜像..."
    docker build --no-cache -f docker/frontend.Dockerfile -t sd-multiplayer-frontend:test . || {
        echo -e "${RED}❌ 前端镜像构建失败${NC}"
        echo "请检查 Dockerfile 和构建上下文"
        echo "如果是 buildx 问题，请参考解决方案"
        exit 1
    }
    echo -e "${GREEN}✓ 前端镜像构建成功${NC}"
    
    # 恢复默认设置
    unset DOCKER_BUILDKIT
}

# 创建测试环境
setup_test_env() {
    echo "🔧 创建测试环境..."
    
    # 创建 Docker 网络
    docker network create sd-test-network 2>/dev/null || true
    
    # 创建测试数据目录
    mkdir -p ./test-data/{storage,db}
    chmod 755 ./test-data
}

# 测试后端
test_backend() {
    echo "🚀 启动后端服务..."
    
    docker run -d \
        --name backend-service \
        --network sd-test-network \
        -p 7860:7860 \
        -e STABILITY_API_KEY="${STABILITY_API_KEY:-test-key}" \
        -e LIVEBLOCKS_SECRET="${LIVEBLOCKS_SECRET:-test-secret}" \
        -v $(pwd)/test-data/storage:/app/stablediffusion-infinity/local_storage \
        -v $(pwd)/test-data/db:/app/stablediffusion-infinity/db \
        sd-multiplayer-backend:test || {
        echo -e "${RED}❌ 后端启动失败${NC}"
        docker logs backend-service
        return 1
    }
    
    echo "⏳ 等待后端启动..."
    sleep 30
    
    # 检查后端健康状态
    # echo "🔍 检查后端健康状态..."
    # for i in {1..12}; do
    #     if curl -f http://localhost:7860/server/api/health 2>/dev/null; then
    #         echo -e "${GREEN}✓ 后端健康检查通过${NC}"
    #         return 0
    #     fi
    #     echo "等待中... ($i/12)"
    #     sleep 5
    # done
    
    # echo -e "${RED}❌ 后端健康检查失败${NC}"
    # echo "后端日志："
    # docker logs sd-backend-test
    # return 1
}

# 测试前端
test_frontend() {
    echo "🎨 启动前端服务..."
    
    docker run -d \
        --name sd-frontend-test \
        --network sd-test-network \
        -p 8080:80 \
        sd-multiplayer-frontend:test || {
        echo -e "${RED}❌ 前端启动失败${NC}"
        docker logs sd-frontend-test
        return 1
    }
    
    echo "⏳ 等待前端启动..."
    sleep 10
    
    # 检查前端健康状态
    echo "🔍 检查前端健康状态..."
    for i in {1..6}; do
        if curl -f http://localhost:8080/health 2>/dev/null; then
            echo -e "${GREEN}✓ 前端健康检查通过${NC}"
            return 0
        fi
        echo "等待中... ($i/6)"
        sleep 5
    done
    
    echo -e "${RED}❌ 前端健康检查失败${NC}"
    echo "前端日志："
    docker logs sd-frontend-test
    return 1
}

# 功能测试
test_functionality() {
    echo "🧪 进行功能测试..."
    
    # 测试后端 API
    echo "测试后端 API..."
    
    # 测试健康检查 API  
    echo "- 测试健康检查 API"
    if curl -s http://localhost:7860/server/api/health | grep -q "healthy"; then
        echo -e "${GREEN}  ✓ 健康检查 API 正常${NC}"
    else
        echo -e "${RED}  ❌ 健康检查 API 异常${NC}"
    fi
    
    # 测试房间列表 API
    echo "- 测试房间列表 API"
    if curl -s http://localhost:7860/server/api/rooms | grep -q "room"; then
        echo -e "${GREEN}  ✓ 房间列表 API 正常${NC}"
    else
        echo -e "${RED}  ❌ 房间列表 API 异常${NC}"
    fi
    
    # 测试前端页面
    echo "测试前端页面..."
    
    # 测试首页
    echo "- 测试首页加载"
    if curl -s http://localhost:8080/ | grep -q "html"; then
        echo -e "${GREEN}  ✓ 前端首页正常${NC}"
    else
        echo -e "${RED}  ❌ 前端首页异常${NC}"
    fi
    
    # 测试前端到后端的代理
    echo "- 测试前端到后端代理"
    if curl -s http://localhost:8080/server/api/health | grep -q "healthy"; then
        echo -e "${GREEN}  ✓ 前端代理正常${NC}"
    else
        echo -e "${RED}  ❌ 前端代理异常${NC}"
    fi
}

# 显示运行状态
show_status() {
    echo ""
    echo "📊 当前运行状态："
    echo "================================"
    docker ps --filter "name=backend-service" --filter "name=sd-frontend-test" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo ""
    echo "🌐 访问地址："
    echo "  前端: http://localhost:8080"
    echo "  后端: http://localhost:7860"
    echo "  健康检查: http://localhost:7860/server/api/health"
    echo "  房间列表: http://localhost:7860/server/api/rooms"
    echo ""
    echo "📝 查看日志："
    echo "  后端: docker logs -f backend-service"
    echo "  前端: docker logs -f sd-frontend-test"
    echo ""
    echo "🛑 停止测试："
    echo "  ./test-docker.sh cleanup"
}

# 主函数
main() {
    case "${1:-test}" in
        "cleanup")
            cleanup
            echo -e "${GREEN}✓ 清理完成${NC}"
            ;;
        "test")
            trap cleanup EXIT
            check_env
            # build_images
            setup_test_env
            
            if test_backend && test_frontend; then
                test_functionality
                echo ""
                echo -e "${GREEN}🎉 所有测试通过！${NC}"
                show_status
                echo ""
                echo -e "${YELLOW}按 Ctrl+C 停止测试并清理${NC}"
                # 保持运行状态，等待用户手动停止
                while true; do
                    sleep 30
                    # 检查容器状态
                    if ! docker ps --filter "name=backend-service" --filter "status=running" | grep -q backend-service; then
                        echo -e "${RED}❌ 后端容器意外停止${NC}"
                        break
                    fi
                    if ! docker ps --filter "name=sd-frontend-test" --filter "status=running" | grep -q sd-frontend-test; then
                        echo -e "${RED}❌ 前端容器意外停止${NC}"
                        break
                    fi
                done
            else
                echo -e "${RED}❌ 测试失败${NC}"
                exit 1
            fi
            ;;
        "logs")
            echo "后端日志："
            docker logs backend-service
            echo ""
            echo "前端日志："
            docker logs sd-frontend-test
            ;;
        *)
            echo "用法: $0 [test|cleanup|logs]"
            echo "  test    - 运行完整测试"
            echo "  cleanup - 清理测试环境"
            echo "  logs    - 查看日志"
            ;;
    esac
}

main "$@" 