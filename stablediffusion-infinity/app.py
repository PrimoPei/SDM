# 必要的 import
import io
import os
import shutil
import logging
import sys
import traceback
import time
from pathlib import Path
import uvicorn


# 新增的 import，用于调用外部 API
import base64
import requests

# 用于加载 .env 文件
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, UploadFile, Depends, status, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utils.tasks import repeat_every
from fastapi.responses import JSONResponse
import glob


import numpy as np
from PIL import Image
import gradio as gr
import shortuuid
import re
import subprocess
import sqlite3
import magic # 假设您保留了 create_upload_file 功能

# --- 加载环境变量 ---
load_dotenv()
STABILITY_API_KEY = os.environ.get("STABILITY_API_KEY")
LIVEBLOCKS_SECRET = os.environ.get("LIVEBLOCKS_SECRET")
# HF_TOKEN = os.environ.get("API_TOKEN") or True # huggingface_hub repo 可能仍需

# --- 日志和路径配置 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)

from logging.handlers import RotatingFileHandler

# 1. 定义日志文件的名称和路径
# LOG_FILENAME = "app.log"

# # 2. 创建一个全局的 logger
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)

# # 3. 创建一个格式化器，定义日志的输出格式
# formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# # 4. 创建一个文件处理器 (FileHandler)，用于写入日志文件
# #    使用 RotatingFileHandler 实现日志轮转，防止日志文件无限增大
# #    maxBytes=5*1024*1024 表示单个文件最大5MB，backupCount=3 表示最多保留3个备份
# file_handler = RotatingFileHandler(LOG_FILENAME, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
# file_handler.setFormatter(formatter)

# # 5. 创建一个流处理器 (StreamHandler)，用于在控制台打印日志
# stream_handler = logging.StreamHandler(sys.stdout)
# stream_handler.setFormatter(formatter)

# # 6. 为 logger 添加这两个处理器
# logger.addHandler(file_handler)
# logger.addHandler(stream_handler)
# --- 日志配置结束 ---





LOCAL_STORAGE_PATH = Path("local_storage")
GALLERY_PATH = LOCAL_STORAGE_PATH / "gallery"
DEFAULT_BACKGROUND_IMAGE = "city.webp" 

ROOM_DB = Path("rooms.db")
ROOMS_DATA_DB = Path("rooms_data.db")  # 添加缺失的数据库定义


# --- FastAPI 应用实例 ---
app = FastAPI()

# --- 中间件和之前的API端点 (保留) ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    if "upgrade" in request.headers and request.headers["upgrade"] == "websocket":
        logger.info(f"!!! 收到 WebSocket 握手请求: {request.method} {request.url}")
    else:
        logger.info(f"收到 HTTP 请求: {request.method} {request.url}")
    response = await call_next(request)
    return response

# --- 您原有的所有辅助函数和API端点都应保留在这里 ---

# 数据库连接函数
def get_room_db():
    db = sqlite3.connect(ROOM_DB, check_same_thread=False)
    db.row_factory = sqlite3.Row
    try:
        yield db
    except Exception:
        db.rollback()
    finally:
        db.close()

def get_room_data_db():
    db = sqlite3.connect(ROOMS_DATA_DB, check_same_thread=False)
    db.row_factory = sqlite3.Row
    try:
        yield db
    except Exception:
        db.rollback()
    finally:
        db.close()

# slugify 工具函数
def slugify(value):
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    out = re.sub(r'[-\s]+', '-', value)
    return out[:400]

# liveblocks 房间用户数获取
def get_room_count(room_id: str):
    try:
        response = requests.get(
            f"https://api.liveblocks.io/v2/rooms/{room_id}/active_users",
            headers={
                "Authorization": f"Bearer {LIVEBLOCKS_SECRET}", 
                "Content-Type": "application/json"
            }
        )

        if response.status_code == 200:
            res = response.json()
            return len(res.get("data", []))
        
        else:
            raise Exception(
                f"获取房间 '{room_id}' 用户数失败。状态码: {response.status_code}, 原因: {response.text}"
            )

    except requests.exceptions.RequestException as e:
        raise Exception(f"请求 Liveblocks API 时发生网络错误: {e}")


# 定时任务
@app.on_event("startup")
@repeat_every(seconds=100)
def sync_rooms():
    logger.info("Syncing rooms active users")
    try:
        for db in get_room_db():
            cursor = db.cursor()
            rooms = cursor.execute("SELECT * FROM rooms").fetchall()
            
            for row in rooms:
                room_id = row["room_id"]
                try:
                    users_count = get_room_count(room_id)
                    
                    cursor.execute(
                        "UPDATE rooms SET users_count = ? WHERE room_id = ?", 
                        (users_count, room_id)
                    )
                except Exception as e:
                    if "404" in str(e):
                        pass
                        logger.warning(f"警告：房间 '{room_id}' 在 Liveblocks 上未找到，将跳过此房间。")
                    else:
                        logger.error(f"处理房间 '{room_id}' 时发生严重错误，请检查: {e}")
            
            db.commit()
            logger.info("房间同步任务完成！")

    except Exception as e:
        logger.error(f"发生数据库级别错误: {e}")
        logger.error(traceback.format_exc())



# 您原有的 API 端点
@app.get('/server/api/room_data/{room_id}')
async def get_rooms_data(room_id: str, start: str = None, end: str = None, db: sqlite3.Connection = Depends(get_room_data_db)):
    logger.info(f"Getting rooms data for room: {room_id}")
    # ... (rest of the function logic is unchanged)
    if start is None and end is None:
        rooms_rows = db.execute(
            "SELECT key, prompt, time, x, y FROM rooms_data WHERE room_id = ? ORDER BY time", (room_id,)).fetchall()
    elif end is None:
        rooms_rows = db.execute("SELECT key, prompt, time, x, y FROM rooms_data WHERE room_id = ? AND time >= ? ORDER BY time",
                                (room_id, start)).fetchall()
    elif start is None:
        rooms_rows = db.execute("SELECT key, prompt, time, x, y FROM rooms_data WHERE room_id = ? AND time <= ? ORDER BY time",
                                (room_id, end)).fetchall()
    else:
        rooms_rows = db.execute("SELECT key, prompt, time, x, y FROM rooms_data WHERE room_id = ? AND time >= ? AND time <= ? ORDER BY time",
                                (room_id, start, end)).fetchall()
    return rooms_rows


@app.get('/server/api/health')
async def health_check():
    """简单的健康检查端点"""
    return {"status": "healthy", "service": "sd-multiplayer-backend"}

@app.get('/server/api/rooms')
async def get_rooms(db: sqlite3.Connection = Depends(get_room_db)):
    logger.info("Getting all rooms")
    rooms = db.execute("SELECT * FROM rooms").fetchall()
    return rooms


@app.post('/server/api/auth')
async def autorize(request: Request):
    data = await request.json()
    room = data["room"]
    payload = {
        "userId": str(shortuuid.uuid()),
        "userInfo": {
            "name": "Anon"
        }}

    response = requests.post(f"https://api.liveblocks.io/v2/rooms/{room}/authorize",
                             headers={"Authorization": f"Bearer {LIVEBLOCKS_SECRET}"}, json=payload)
    if response.status_code == 200:
        sync_rooms()
        return response.json()
    else:
        raise Exception(response.status_code, response.text)


# 保留上传社区文件的功能
FILE_TYPES = {
    'image/png': 'png',
    'image/jpeg': 'jpg',
    'image/webp': 'webp',
}
@app.post('/server/api/uploadfile')
async def create_upload_file(file: UploadFile):
    # --- MONITORING: Monitor file operations ---
    full_path = None
    try:
        contents = await file.read()
        file_size = len(contents)
        if not 0 < file_size < 100E+06:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Supported file size is less than 2 MB'
            )
        file_type = magic.from_buffer(contents, mime=True)
        if file_type.lower() not in FILE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Unsupported file type {file_type}. Supported types are {FILE_TYPES}'
            )

        relative_path = Path("community") / file.filename
        full_path = LOCAL_STORAGE_PATH / relative_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, "wb") as f:
            f.write(contents)

        return {"url": f'/storage/{relative_path.as_posix()}', "filename": file.filename}
    except (IOError, PermissionError) as e:
        path_str = str(full_path) if full_path else "Unknown"
        logger.error(f"社区文件上传失败！检查磁盘空间或文件夹权限。路径: {path_str}. 错误: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Could not save file.")
    # --- MONITORING END ---

    
# 保留获取默认背景图的API
@app.get("/server/api/default_background")
async def get_default_background():
    """
    返回预设的、唯一的默认背景图的URL。
    """
    logger.info("收到获取默认背景图的请求。")
    try:
        # 构造默认图片的完整路径
        default_image_path = GALLERY_PATH / DEFAULT_BACKGROUND_IMAGE

        # 检查文件是否存在，以防配置错误
        if not default_image_path.is_file():
            logger.error(f"预设的默认背景图未找到！路径: {default_image_path}")
            return JSONResponse(status_code=404, content={"error": "默认背景图未在服务器上找到。"})

        # 构建可供前端访问的URL
        image_url = f"/storage/gallery/{DEFAULT_BACKGROUND_IMAGE}"

        # 以 JSON 格式返回这个唯一的URL
        return JSONResponse(content={"url": image_url})

    except Exception as e:
        logger.error(f"获取默认背景图时发生错误: {e}")
        logger.error(traceback.format_exc())
        return JSONResponse(status_code=500, content={"error": "无法检索默认背景图。"})


# --- 核心改动：用 API 版本替换本地模型 ---

# 本地模型加载函数 get_model() 已被完全删除

# 上传/保存文件的辅助函数 (保持不变)
async def upload_file(image: Image.Image, prompt: str, room_id: str, image_key: str):
    image_to_save = image.convert('RGB')
    id = shortuuid.uuid()
    date = int(time.time())
    prompt_slug = slugify(prompt)
    filename = f"{date}-{id}-{image_key}-{prompt_slug}.webp"
    timelapse_name = f"{id}.webp"
    key_name = f"{room_id}/{filename}"
    
    full_path = LOCAL_STORAGE_PATH / key_name
    timelapse_dir = LOCAL_STORAGE_PATH / "timelapse" / room_id
    timelapse_path = timelapse_dir / timelapse_name
    
    full_path.parent.mkdir(parents=True, exist_ok=True)
    timelapse_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        image_to_save.save(full_path, format="WEBP")
        shutil.copy(full_path, timelapse_path)
    except (IOError, PermissionError) as e:
        logger.error(f"文件写入失败！路径: {full_path}. 错误: {e}")
        logger.error(traceback.format_exc())
        raise

    out = {"url": f'/storage/{key_name}', "filename": filename}
    return out

# 全新重写的 run_outpaint 函数，用于调用外部 API
async def run_outpaint(
    input_image,
    prompt_text,
    strength,
    guidance,
    step,
    fill_mode,
    room_id,
    image_key
):
    request_id = shortuuid.uuid()[:8]
    logger.info(f"[Request ID: {request_id}] 收到 API 请求。目标尺寸: {input_image.size}")
    start_time = time.time()

    if not STABILITY_API_KEY:
        error_msg = "错误：服务器未配置 STABILITY_API_KEY。"
        logger.error(f"[Request ID: {request_id}] {error_msg}")
        raise Exception(error_msg)

    # --- START OF MODIFICATION ---
    # 1. 保存前端期望的目标尺寸
    target_size = input_image.size  # 例如 (1920, 1080)
    # --- END OF MODIFICATION ---

    api_url = "https://api.stability.ai/v2beta/stable-image/generate/sd3"
    headers = { "Authorization": f"Bearer {STABILITY_API_KEY}", "Accept": "application/json" }
    payload = { "model": "sd3.5-medium", "prompt": prompt_text, "output_format": "png", "steps": int(step), "cfg_scale": guidance }
    files = {}
    img_np = np.array(input_image.convert("RGB"))

    if np.std(img_np) < 10:
        payload['mode'] = 'text-to-image'
        # 在文生图模式下，我们可以尝试让API生成更接近的宽高比
        # 这里做一个简单的判断
        if target_size[0] > target_size[1]:
            payload['aspect_ratio'] = "16:9"
        elif target_size[1] > target_size[0]:
            payload['aspect_ratio'] = "9:16"
        else:
            payload['aspect_ratio'] = "1:1"
        logger.info(f"[Request ID: {request_id}] 空白画布，使用 'text-to-image' 模式。请求宽高比: {payload['aspect_ratio']}")

    else:
        logger.info(f"[Request ID: {request_id}] 有内容画布，使用 'image-to-image' 模式。")
        payload['mode'] = 'image-to-image'
        payload['strength'] = strength
        image_bytes = io.BytesIO()
        input_image.save(image_bytes, format='PNG')
        image_bytes.seek(0)
        files['image'] = ('init_image.png', image_bytes)

    logger.info(f"[Request ID: {request_id}] 正在调用 Stability API...")

    try:
        response = requests.post(api_url, headers=headers, data=payload, files=files)
        response.raise_for_status()
        api_result = response.json()
        logger.info(f"[Request ID: {request_id}] API 响应原始数据: {api_result}")

        image_artifact = None
        if "artifacts" in api_result and isinstance(api_result.get("artifacts"), list) and len(api_result["artifacts"]) > 0:
            image_artifact = api_result["artifacts"][0]
        elif "image" in api_result:
            image_artifact = api_result
        if image_artifact is None: raise Exception("无法在API响应中定位 artifact 对象。")

        base64_image_data = image_artifact.get("image") or image_artifact.get("base64")
        if not base64_image_data: raise Exception("在 artifact 中未找到图像数据键。")

        image_bytes = base64.b64decode(base64_image_data)
        generated_image = Image.open(io.BytesIO(image_bytes))
        logger.info(f"[Request ID: {request_id}] 从API接收到图片，原始尺寸: {generated_image.size}")

        # --- START OF MODIFICATION ---
        # 2. 将API返回的图片缩放到目标尺寸
        #    Image.Resampling.LANCZOS 是高质量的缩放算法
        try:
            resampling_filter = Image.Resampling.LANCZOS
        except AttributeError: # 兼容旧版 Pillow
            resampling_filter = Image.LANCZOS
            
        resized_image = generated_image.resize(target_size, resampling_filter)
        logger.info(f"[Request ID: {request_id}] 图片已缩放至目标尺寸: {resized_image.size}")
        # --- END OF MODIFICATION ---

        # 3. 将缩放后的图片传递给保存函数
        image_url_data = await upload_file(resized_image, prompt_text, room_id, image_key)

        finish_reason = image_artifact.get("finishReason") or image_artifact.get("finish_reason")
        params = {
            "is_nsfw": finish_reason == 'CONTENT_FILTERED',
            "image": image_url_data
        }
        
        duration = time.time() - start_time
        logger.info(f"[Request ID: {request_id}] API 调用成功并处理完毕。耗时: {duration:.2f} 秒。")
        return params

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"[Request ID: {request_id}] 调用API时发生错误。耗时: {duration:.2f} 秒。")
        if 'response' in locals() and response:
            logger.error(f"API 响应内容: {response.text}")
        logger.error(traceback.format_exc())
        return {"is_nsfw": True, "image": {}}

        
# --- Gradio 接口 (保持不变) ---
try:
    SAMPLING_MODE = Image.Resampling.LANCZOS
except Exception as e:
    SAMPLING_MODE = Image.LANCZOS
    
with gr.Blocks().queue() as blocks:
    with gr.Row():
        with gr.Column(scale=3, min_width=270):
            sd_prompt = gr.Textbox(label="Prompt", placeholder="input your prompt here", lines=4)
        with gr.Column(scale=2, min_width=150):
            sd_strength = gr.Slider(label="Strength", minimum=0.0, maximum=1.0, value=0.75, step=0.01)
        with gr.Column(scale=1, min_width=150):
            sd_step = gr.Number(label="Step", value=50, precision=0)
            sd_guidance = gr.Number(label="Guidance", value=7.5)
    with gr.Row():
        with gr.Column(scale=4, min_width=600):
            init_mode = gr.Radio(
                label="Init mode",
                choices=["patchmatch", "edge_pad", "cv2_ns", "cv2_telea", "gaussian", "perlin"],
                value="patchmatch",
                type="value",
            )

    model_input = gr.Image(label="Input", type="pil", image_mode="RGBA")
    room_id = gr.Textbox(label="Room ID")
    image_key = gr.Textbox(label="image_key")
    proceed_button = gr.Button("Proceed", elem_id="proceed")
    params = gr.JSON()

    proceed_button.click(
        fn=run_outpaint,
        inputs=[model_input, sd_prompt, sd_strength, sd_guidance, sd_step, init_mode, room_id, image_key],
        outputs=[params],
    )

# --- FastAPI 挂载和启动 (保持不变) ---
app = gr.mount_gradio_app(app, blocks, "/gradio", gradio_api_url="http://0.0.0.0:7860/gradio/")

app.mount("/storage", StaticFiles(directory=LOCAL_STORAGE_PATH), name="storage")
# 注意：在容器化部署中，前端由独立的 Nginx 容器提供服务
# app.mount("/", StaticFiles(directory="../frontend/build", html=True), name="static")

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    # 确保文件夹存在
    LOCAL_STORAGE_PATH.mkdir(exist_ok=True)
    GALLERY_PATH.mkdir(exist_ok=True)
    
    # 检查数据库文件
    if not ROOM_DB.exists():
        logger.info("正在创建主数据库...")
        db = sqlite3.connect(ROOM_DB)
        # 假设 schema.sql 在同一目录
        if Path("schema.sql").exists():
            with open(Path("schema.sql"), "r") as f:
                db.executescript(f.read())
            db.commit()
            logger.info("主数据库创建成功。")
        else:
            logger.warning("未找到 schema.sql, 数据库为空。")
        db.close()

    logger.info(f"服务器启动，文件将保存在本地目录: {LOCAL_STORAGE_PATH.resolve()}")
    uvicorn.run(app, host="0.0.0.0", port=7860, log_level="info", reload=False)