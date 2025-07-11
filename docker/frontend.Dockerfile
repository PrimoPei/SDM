# 前端服务 Dockerfile - Svelte 应用构建和 Nginx 服务
# 第一阶段：构建 Svelte 应用
FROM node:18-alpine AS builder

WORKDIR /app

# 复制 package 文件并安装依赖
COPY frontend/package*.json ./
RUN npm ci

# 复制前端代码
COPY frontend/ .

# 创建环境配置文件（如果需要）
RUN if [ ! -f .env ]; then \
        echo "# 生产环境配置" > .env; \
    fi

# 构建应用
RUN npm run build

# 第二阶段：Nginx 服务
FROM nginx:alpine

# 复制自定义 Nginx 配置
COPY docker/nginx.conf /etc/nginx/nginx.conf

# 从构建阶段复制构建产物
COPY --from=builder /app/build /usr/share/nginx/html

# 创建日志目录
RUN mkdir -p /var/log/nginx

# 暴露端口
EXPOSE 80

# 启动 Nginx
CMD ["nginx", "-g", "daemon off;"] 