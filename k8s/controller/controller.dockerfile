FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装
# 您需要创建一个 requirements.txt 文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制 Controller 代码
COPY controller.py .

# 运行 Controller
CMD ["python", "controller.py"]