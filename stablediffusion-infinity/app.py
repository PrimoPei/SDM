import io
import os
import shutil
# --- MONITORING ---
import logging
import sys
import traceback
import time
# --- MONITORING END ---
import numpy as np
from huggingface_hub import Repository

from pathlib import Path
import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, Depends, status, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utils.tasks import repeat_every

import numpy as np
import torch
from torch import autocast
from diffusers import StableDiffusionInpaintPipeline, EulerAncestralDiscreteScheduler
from diffusers.models import AutoencoderKL

from PIL import Image
import gradio as gr
import skimage
import skimage.measure
from utils import *
# import boto3 # No longer needed for local storage
import magic
import sqlite3
import requests
import shortuuid
import re
import subprocess

# --- MONITORING: Setup Logging ---
# 配置日志记录器
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout,  # 输出到控制台
)
logger = logging.getLogger(__name__)
# --- MONITORING END ---

# AWS credentials are no longer needed
LIVEBLOCKS_SECRET = os.environ.get("LIVEBLOCKS_SECRET")
HF_TOKEN = os.environ.get("API_TOKEN") or True

LOCAL_STORAGE_PATH = Path("local_storage")

FILE_TYPES = {
    'image/png': 'png',
    'image/jpeg': 'jpg',
    'imager/webp': 'webp',
}
S3_DATA_FOLDER = Path("sd-multiplayer-data")
ROOMS_DATA_DB = S3_DATA_FOLDER / "rooms_data.db"
ROOM_DB = Path("rooms.db")

app = FastAPI()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    # 针对 WebSocket 的初始 HTTP Upgrade 请求进行日志记录
    if "upgrade" in request.headers and request.headers["upgrade"] == "websocket":
        logger.info(f"!!! 收到 WebSocket 握手请求: {request.method} {request.url}")
    else:
        logger.info(f"收到 HTTP 请求: {request.method} {request.url}")

    response = await call_next(request)
    return response


repo = Repository(
    local_dir=S3_DATA_FOLDER,
    repo_type="dataset",
    clone_from="huggingface-projects/sd-multiplayer-data",
    use_auth_token=True,
)

if not ROOM_DB.exists():
    print("Creating database")
    print("ROOM_DB", ROOM_DB)
    db = sqlite3.connect(ROOM_DB)
    with open(Path("schema.sql"), "r") as f:
        db.executescript(f.read())
    db.commit()
    db.close()


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


try:
    SAMPLING_MODE = Image.Resampling.LANCZOS
except Exception as e:
    SAMPLING_MODE = Image.LANCZOS


blocks = gr.Blocks().queue()
model = {}

STATIC_MASK = Image.open("mask.png")


def sync_rooms_data_repo():
    subprocess.Popen("git fetch && git reset --hard origin/main",
                     cwd=S3_DATA_FOLDER, shell=True)


def get_model():
    # --- MONITORING: Monitor model loading ---
    if "inpaint" not in model:
        logger.info("开始加载 Stable Diffusion Inpainting 模型...")
        start_time = time.time()
        try:
            scheduler = EulerAncestralDiscreteScheduler.from_pretrained(
                "stabilityai/stable-diffusion-2-base", subfolder="scheduler")
            inpaint = StableDiffusionInpaintPipeline.from_pretrained(
                "stabilityai/stable-diffusion-2-inpainting",
                torch_dtype=torch.float32,
            )
            inpaint.scheduler = scheduler
            inpaint = inpaint.to("cuda")
            model["inpaint"] = inpaint
            duration = time.time() - start_time
            logger.info(f"模型加载成功！耗时: {duration:.2f} 秒。")
        except Exception as e:
            logger.critical("!!!!!! 模型加载失败，服务器无法启动 !!!!!!")
            logger.critical(traceback.format_exc())
            # 关键错误，直接退出程序
            sys.exit(1)
    # --- MONITORING END ---
    return model["inpaint"]


# init model on startup
get_model()


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
    # 1. 为每个请求生成唯一ID，方便追踪日志
    request_id = shortuuid.uuid()[:8]
    logger.info(f"[Request ID: {request_id}] 收到图像生成请求。Room: '{room_id}', Key: '{image_key}'")
    start_time = time.time()
    
    try:
        inpaint = get_model()
        
        sel_buffer = np.array(input_image)
        img = sel_buffer[:, :, 0:3]
        mask = sel_buffer[:, :, -1]

        # 2. 空白画布检测与处理：如果输入是纯白或纯色，则替换为随机噪声
        if np.std(img) < 10:
            logger.info(f"[Request ID: {request_id}] 检测到空白或纯色画布，将使用随机噪声作为初始图像。")
            img = np.random.randint(0, 256, img.shape, dtype=np.uint8)

        # nmask = 255 - mask

        nmask = mask.copy()
        process_size = 512
        negative_syntax = r'\<(.*?)\>'
        prompt = re.sub(negative_syntax, ' ', prompt_text)
        negative_prompt = ' '.join(re.findall(negative_syntax, prompt_text))
        
        # 3. 蒙版处理逻辑（已经移除了 `mask = 255 - mask` 的错误反转操作）
        if nmask.sum() < 1:
            logger.info(f"[Request ID: {request_id}] 使用预设的静态蒙版进行绘制。")
            mask = np.array(STATIC_MASK)[:, :, 0]
            img, mask = functbl[fill_mode](img, mask)
            init_image = Image.fromarray(img)
            mask = skimage.measure.block_reduce(mask, (8, 8), np.max)
            mask = mask.repeat(8, axis=0).repeat(8, axis=1)
            mask_image = Image.fromarray(mask)
        elif mask.sum() > 0:
            logger.info(f"[Request ID: {request_id}] 使用用户手绘的蒙版进行绘制。")
            img, mask = functbl[fill_mode](img, mask)
            init_image = Image.fromarray(img)
            mask = skimage.measure.block_reduce(mask, (8, 8), np.max)
            mask = mask.repeat(8, axis=0).repeat(8, axis=1)
            mask_image = Image.fromarray(mask)
        else:
            logger.info(f"[Request ID: {request_id}] 无蒙版，执行文生图模式。")
            img, mask = functbl[fill_mode](img, mask)
            init_image = Image.fromarray(img)
            mask = skimage.measure.block_reduce(mask, (8, 8), np.max)
            mask = mask.repeat(8, axis=0).repeat(8, axis=1)
            mask_image = Image.fromarray(mask)

        # 4. GPU显存监控（推理前）
        if torch.cuda.is_available():
            logger.info(f"[Request ID: {request_id}] 推理前 - 已分配GPU显存: {torch.cuda.memory_allocated(0)/1024**2:.2f} MB")
            logger.info(f"[Request ID: {request_id}] 推理前 - 已保留GPU显存: {torch.cuda.memory_reserved(0)/1024**2:.2f} MB")
        
        # (可选的调试步骤) 如果还需要调试蒙版，可以取消下面代码的注释
        # debug_path = Path("debug_images")
        # debug_path.mkdir(exist_ok=True)
        # init_image.resize((process_size, process_size)).save(debug_path / f"{request_id}_init_image.png")
        # mask_image.resize((process_size, process_size)).save(debug_path / f"{request_id}_mask_image.png")
        # logger.info(f"已将调试图片保存在 {debug_path.resolve()} 文件夹中。")
        
        output = None
        with autocast("cuda"):
            try:
                # 5. 核心推理步骤
                output = inpaint(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    image=init_image.resize((process_size, process_size), resample=SAMPLING_MODE),
                    mask_image=mask_image.resize((process_size, process_size)),
                    strength=strength,
                    num_inference_steps=int(step),
                    guidance_scale=guidance,
                )
            except torch.cuda.OutOfMemoryError:
                logger.error(f"[Request ID: {request_id}] !!! GPU显存不足 (Out of Memory) !!!")
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                raise
            except Exception as inference_e:
                logger.error(f"[Request ID: {request_id}] 推理过程中发生未知错误: {inference_e}")
                logger.error(traceback.format_exc())
                raise
        
        # 6. GPU显存监控（推理后）
        if torch.cuda.is_available():
            logger.info(f"[Request ID: {request_id}] 推理后 - 已分配GPU显存: {torch.cuda.memory_allocated(0)/1024**2:.2f} MB")
        
        image = output["images"][0]
        is_nsfw = output.get("nsfw_content_detected", [False])[0]
        image_url = {}

        if not is_nsfw:
            # 调用我们之前修复好的 upload_file 函数，它内部包含了从浮点数到整数的转换
            image_url = await upload_file(image, prompt + "NNOTN" + negative_prompt, room_id, image_key)

        params = {
            "is_nsfw": is_nsfw,
            "image": image_url
        }
        
        duration = time.time() - start_time
        logger.info(f"[Request ID: {request_id}] 图像生成成功完成。耗时: {duration:.2f} 秒。")
        
        return params

    except Exception as e:
        # 7. 兜底的异常处理
        duration = time.time() - start_time
        logger.error(f"[Request ID: {request_id}] 'run_outpaint' 函数处理失败。耗时: {duration:.2f} 秒。错误: {e}")
        logger.error(traceback.format_exc())
        # 返回一个表示失败的JSON结构，防止前端崩溃
        return {"is_nsfw": True, "image": {}}

with blocks as demo:

    with gr.Row():

        with gr.Column(scale=3, min_width=270):
            sd_prompt = gr.Textbox(
                label="Prompt", placeholder="input your prompt here", lines=4
            )
        with gr.Column(scale=2, min_width=150):
            sd_strength = gr.Slider(
                label="Strength", minimum=0.0, maximum=1.0, value=0.75, step=0.01
            )
        with gr.Column(scale=1, min_width=150):
            sd_step = gr.Number(label="Step", value=100, precision=0)
            sd_guidance = gr.Number(label="Guidance", value=7)
    with gr.Row():
        with gr.Column(scale=4, min_width=600):
            init_mode = gr.Radio(
                label="Init mode",
                choices=[
                    "patchmatch",
                    "edge_pad",
                    "cv2_ns",
                    "cv2_telea",
                    "gaussian",
                    "perlin",
                ],
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
        inputs=[
            model_input,
            sd_prompt,
            sd_strength,
            sd_guidance,
            sd_step,
            init_mode,
            room_id,
            image_key
        ],
        outputs=[params],
    )


blocks.config['dev_mode'] = False

app = gr.mount_gradio_app(app, blocks, "/gradio",
                         gradio_api_url="http://0.0.0.0:7860/gradio/")


def generateAuthToken():
    response = requests.get(f"https://liveblocks.io/api/authorize",
                            headers={"Authorization": f"Bearer {LIVEBLOCKS_SECRET}"})
    if response.status_code == 200:
        data = response.json()
        return data["token"]
    else:
        raise Exception(response.status_code, response.text)


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
                        #logger.warning(f"警告：房间 '{room_id}' 在 Liveblocks 上未找到，将跳过此房间。")
                    else:
                        logger.error(f"处理房间 '{room_id}' 时发生严重错误，请检查: {e}")
            
            db.commit()
            logger.info("房间同步任务完成！")

    except Exception as e:
        logger.error(f"发生数据库级别错误: {e}")
        logger.error(traceback.format_exc())



@app.on_event("startup")
@repeat_every(seconds=300)
def sync_room_datq():
    logger.info("Sync rooms data")
    sync_rooms_data_repo()


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


def slugify(value):
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    out = re.sub(r'[-\s]+', '-', value)
    return out[:400]


async def upload_file(image: Image.Image, prompt: str, room_id: str, image_key: str):
    # --- START OF MODIFICATION ---
    # 我们不再需要 NumPy 转换，直接使用模型输出的原始 PIL Image 对象
    # 因为我们现在相信在 float32 模式下，它的数据范围是正确的。
    
    room_id = room_id.strip() or "uploads"
    image_key = image_key.strip() or ""
    
    # 为确保兼容性，最好还是做一次颜色模式转换
    image_to_save = image.convert('RGB')

    # 生成文件名等信息
    id = shortuuid.uuid()
    date = int(time.time())
    prompt_slug = slugify(prompt)
    filename = f"{date}-{id}-{image_key}-{prompt_slug}.webp"
    timelapse_name = f"{id}.webp"
    key_name = f"{room_id}/{filename}"
    
    # 定义本地保存路径
    full_path = LOCAL_STORAGE_PATH / key_name
    timelapse_dir = LOCAL_STORAGE_PATH / "timelapse" / room_id
    timelapse_path = timelapse_dir / timelapse_name
    
    full_path.parent.mkdir(parents=True, exist_ok=True)
    timelapse_dir.mkdir(parents=True, exist_ok=True)
    
    # 直接保存从模型中得到的、经过RGB转换的图片
    try:
        image_to_save.save(full_path, format="WEBP")
        shutil.copy(full_path, timelapse_path)
    except (IOError, PermissionError) as e:
        logger.error(f"文件写入失败！检查磁盘空间或文件夹权限。路径: {full_path}. 错误: {e}")
        logger.error(traceback.format_exc())
        raise

    out = {"url": f'/storage/{key_name}', "filename": filename}
    return out
    # --- END OF MODIFICATION ---

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

app.mount("/storage", StaticFiles(directory=LOCAL_STORAGE_PATH), name="storage")
app.mount("/", StaticFiles(directory="../static", html=True), name="static")


origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


if __name__ == "__main__":
    # --- MONITORING: Ensure the base storage directory exists on startup ---
    LOCAL_STORAGE_PATH.mkdir(exist_ok=True)
    logger.info(f"服务器启动，文件将保存在本地目录: {LOCAL_STORAGE_PATH.resolve()}")
    
    uvicorn.run(app, host="0.0.0.0", port=7860,
                log_level="info", reload=False)