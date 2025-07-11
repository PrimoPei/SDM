#!/bin/bash

echo "🚀 快速测试当前环境..."

# 检查容器运行状态
echo "1. 检查运行的容器："
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | head -10

echo -e "\n2. 测试后端健康检查："
curl -s http://localhost:7860/server/api/health | jq . 2>/dev/null || curl -s http://localhost:7860/server/api/health

echo -e "\n3. 测试后端房间列表："
curl -s http://localhost:7860/server/api/rooms | jq . 2>/dev/null || curl -s http://localhost:7860/server/api/rooms

echo -e "\n4. 测试前端健康检查："
curl -s http://localhost:8080/health

echo -e "\n5. 测试前端代理（房间列表）："
curl -s http://localhost:8080/server/api/health | jq . 2>/dev/null || curl -s http://localhost:8080/server/api/health

echo -e "\n6. 检查端口监听："
ss -tulpn | grep -E ":(7860|8080|8081)" || netstat -tulpn | grep -E ":(7860|8080|8081)"

echo -e "\n7. 检查最近的错误日志："
echo "后端日志（最近5行）："
docker logs --tail 15 backend-service 2>/dev/null || echo "后端容器未运行"

echo -e "\n前端日志（最近5行）："
docker logs --tail 15 sd-frontend-test 2>/dev/null || echo "前端容器未运行"

echo -e "\n✅ 测试完成！"
echo "如果看到错误，请检查："
echo "1. 容器是否正常运行"
echo "2. 端口是否正确（前端应该是8080，后端是7860）"
echo "3. API 响应是否正常" 