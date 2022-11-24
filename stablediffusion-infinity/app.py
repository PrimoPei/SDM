import io
import os

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
from diffusers import StableDiffusionInpaintPipeline
from diffusers.models import AutoencoderKL

from PIL import Image
import gradio as gr
import skimage
import skimage.measure
from utils import *
import boto3
import magic
import sqlite3
import requests
import shortuuid
import re
import time
import subprocess

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
AWS_S3_BUCKET_NAME = os.getenv('AWS_S3_BUCKET_NAME')
LIVEBLOCKS_SECRET = os.environ.get("LIVEBLOCKS_SECRET")
HF_TOKEN = os.environ.get("API_TOKEN") or True

FILE_TYPES = {
    'image/png': 'png',
    'image/jpeg': 'jpg',
    'imager/webp': 'webp',
}
S3_DATA_FOLDER = Path("sd-multiplayer-data")
ROOMS_DATA_DB = S3_DATA_FOLDER / "rooms_data.db"
ROOM_DB = Path("rooms.db")

app = FastAPI()

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


s3 = boto3.client(service_name='s3',
                  aws_access_key_id=AWS_ACCESS_KEY_ID,
                  aws_secret_access_key=AWS_SECRET_KEY)
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
    if "inpaint" not in model:
        vae = AutoencoderKL.from_pretrained(f"stabilityai/sd-vae-ft-ema")
        inpaint = StableDiffusionInpaintPipeline.from_pretrained(
            "radames/stable-diffusion-v2-inpainting",
            torch_dtype=torch.float16,
            vae=vae,
        ).to("cuda")
        model["inpaint"] = inpaint

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
    inpaint = get_model()
    sel_buffer = np.array(input_image)
    img = sel_buffer[:, :, 0:3]
    mask = sel_buffer[:, :, -1]
    nmask = 255 - mask
    process_size = 512

    if nmask.sum() < 1:
        print("inpaiting with fixed Mask")
        mask = np.array(STATIC_MASK)[:, :, 0]
        img, mask = functbl[fill_mode](img, mask)
        init_image = Image.fromarray(img)
        mask = 255 - mask
        mask = skimage.measure.block_reduce(mask, (8, 8), np.max)
        mask = mask.repeat(8, axis=0).repeat(8, axis=1)
        mask_image = Image.fromarray(mask)
    elif mask.sum() > 0:
        print("inpainting")
        img, mask = functbl[fill_mode](img, mask)
        init_image = Image.fromarray(img)
        mask = 255 - mask
        mask = skimage.measure.block_reduce(mask, (8, 8), np.max)
        mask = mask.repeat(8, axis=0).repeat(8, axis=1)
        mask_image = Image.fromarray(mask)

        # mask_image=mask_image.filter(ImageFilter.GaussianBlur(radius = 8))
    else:
        print("text2image")
        print("inpainting")
        img, mask = functbl[fill_mode](img, mask)
        init_image = Image.fromarray(img)
        mask = 255 - mask
        mask = skimage.measure.block_reduce(mask, (8, 8), np.max)
        mask = mask.repeat(8, axis=0).repeat(8, axis=1)
        mask_image = Image.fromarray(mask)

        # mask_image=mask_image.filter(ImageFilter.GaussianBlur(radius = 8))
    with autocast("cuda"):
        output = inpaint(
            prompt=prompt_text,
            image=init_image.resize(
                (process_size, process_size), resample=SAMPLING_MODE
            ),
            mask_image=mask_image.resize((process_size, process_size)),
            strength=strength,
            num_inference_steps=step,
            guidance_scale=guidance,
        )
    image = output["images"][0]
    is_nsfw = output["nsfw_content_detected"][0]
    image_url = {}

    if not is_nsfw:
        # print("not nsfw, uploading")
        image_url = await upload_file(image, prompt_text, room_id, image_key)

    params = {
        "is_nsfw": is_nsfw,
        "image": image_url
    }
    return params


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
            sd_step = gr.Number(label="Step", value=50, precision=0)
            sd_guidance = gr.Number(label="Guidance", value=7.5)
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
    response = requests.get(
        f"https://api.liveblocks.io/v2/rooms/{room_id}/active_users",
        headers={"Authorization": f"Bearer {LIVEBLOCKS_SECRET}", "Content-Type": "application/json"})
    if response.status_code == 200:
        res = response.json()
        if "data" in res:
            return len(res["data"])
        else:
            return 0
    raise Exception("Error getting room count")


@ app.on_event("startup")
@ repeat_every(seconds=100)
def sync_rooms():
    print("Syncing rooms active users")
    try:
        for db in get_room_db():
            rooms = db.execute("SELECT * FROM rooms").fetchall()
            for row in rooms:
                room_id = row["room_id"]
                users_count = get_room_count(room_id)
                cursor = db.cursor()
                cursor.execute(
                    "UPDATE rooms SET users_count = ? WHERE room_id = ?", (users_count, room_id))
                db.commit()
    except Exception as e:
        print(e)
        print("Rooms update failed")


@ app.on_event("startup")
@ repeat_every(seconds=300)
def sync_room_datq():
    print("Sync rooms data")
    sync_rooms_data_repo()


@ app.get('/api/room_data/{room_id}')
async def get_rooms_data(room_id: str, start: str = None, end: str = None, db: sqlite3.Connection = Depends(get_room_data_db)):
    print("Getting rooms data", room_id, start, end)

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


@ app.get('/api/rooms')
async def get_rooms(db: sqlite3.Connection = Depends(get_room_db)):
    print("Getting rooms")
    rooms = db.execute("SELECT * FROM rooms").fetchall()
    return rooms


@ app.post('/api/auth')
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
        # user in, incremente room count
        # cursor = db.cursor()
        # cursor.execute(
        #     "UPDATE rooms SET users_count = users_count + 1 WHERE room_id = ?", (room,))
        # db.commit()
        sync_rooms()
        return response.json()
    else:
        raise Exception(response.status_code, response.text)


def slugify(value):
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    out = re.sub(r'[-\s]+', '-', value)
    return out[:400]


async def upload_file(image: Image.Image, prompt: str, room_id: str, image_key: str):
    room_id = room_id.strip() or "uploads"
    image_key = image_key.strip() or ""
    image = image.convert('RGB')
    # print("Uploading file from predict")
    temp_file = io.BytesIO()
    image.save(temp_file, format="WEBP")
    temp_file.seek(0)
    id = shortuuid.uuid()
    date = int(time.time())
    prompt_slug = slugify(prompt)
    filename = f"{date}-{id}-{image_key}-{prompt_slug}.webp"
    timelapse_name = f"{id}.webp"
    key_name = f"{room_id}/{filename}"
    s3.upload_fileobj(Fileobj=temp_file, Bucket=AWS_S3_BUCKET_NAME, Key=key_name, ExtraArgs={"ContentType": "image/webp", "CacheControl": "max-age=31536000"})
    s3.copy_object(Bucket=AWS_S3_BUCKET_NAME, CopySource=f"{AWS_S3_BUCKET_NAME}/{key_name}", Key=f"timelapse/{room_id}/{timelapse_name}")

    temp_file.close()

    out = {"url": f'https://d26smi9133w0oo.cloudfront.net/{room_id}/{filename}',
           "filename": filename}
    return out


@ app.post('/api/uploadfile')
async def create_upload_file(file: UploadFile):
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
    temp_file = io.BytesIO()
    temp_file.write(contents)
    temp_file.seek(0)
    s3.upload_fileobj(Fileobj=temp_file, Bucket=AWS_S3_BUCKET_NAME, Key="community/" +
                      file.filename, ExtraArgs={"ContentType": file.content_type, "CacheControl": "max-age=31536000"})
    temp_file.close()

    return {"url": f'https://d26smi9133w0oo.cloudfront.net/community/{file.filename}', "filename": file.filename}


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
    uvicorn.run(app, host="0.0.0.0", port=7860,
                log_level="debug", reload=False)
