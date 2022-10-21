import io
import os

from pathlib import Path
import uvicorn
from fastapi import FastAPI, BackgroundTasks, HTTPException, UploadFile, Depends, status, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi_utils.tasks import repeat_every

import numpy as np
import torch
from torch import autocast
from diffusers import StableDiffusionPipeline, StableDiffusionInpaintPipeline
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
import uuid

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
AWS_S3_BUCKET_NAME = os.getenv('AWS_S3_BUCKET_NAME')
LIVEBLOCKS_SECRET = os.environ.get("LIVEBLOCKS_SECRET")
HF_TOKEN = os.environ.get("API_TOKEN") or True

FILE_TYPES = {
    'image/png': 'png',
    'image/jpeg': 'jpg',
}
DB_PATH = Path("rooms.db")

app = FastAPI()

if not DB_PATH.exists():
    print("Creating database")
    print("DB_PATH", DB_PATH)
    db = sqlite3.connect(DB_PATH)
    with open(Path("schema.sql"), "r") as f:
        db.executescript(f.read())


def get_db():
    db = sqlite3.connect(DB_PATH, check_same_thread=False)
    db.row_factory = sqlite3.Row
    print("Connected to database")
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

WHITES = 66846720
STATIC_MASK = Image.open("mask.png")


def get_model():
    if "inpaint" not in model:

        vae = AutoencoderKL.from_pretrained(f"stabilityai/sd-vae-ft-ema")
        inpaint = StableDiffusionInpaintPipeline.from_pretrained(
            "runwayml/stable-diffusion-inpainting",
            revision="fp16",
            torch_dtype=torch.float16,
            vae=vae,
        ).to("cuda")

        # lms = LMSDiscreteScheduler(
        #     beta_start=0.00085, beta_end=0.012, beta_schedule="scaled_linear")

        # img2img = StableDiffusionImg2ImgPipeline(
        #     vae=text2img.vae,
        #     text_encoder=text2img.text_encoder,
        #     tokenizer=text2img.tokenizer,
        #     unet=text2img.unet,
        #     scheduler=lms,
        #     safety_checker=text2img.safety_checker,
        #     feature_extractor=text2img.feature_extractor,
        # ).to("cuda")
        # try:
        #     total_memory = torch.cuda.get_device_properties(0).total_memory // (
        #         1024 ** 3
        #     )
        #     if total_memory <= 5:
        #         inpaint.enable_attention_slicing()
        # except:
        #     pass
        model["inpaint"] = inpaint
        # model["img2img"] = img2img

    return model["inpaint"]
    # model["img2img"]


# init model on startup
get_model()


def run_outpaint(
    input_image,
    prompt_text,
    strength,
    guidance,
    step,
    fill_mode,


):
    inpaint = get_model()
    sel_buffer = np.array(input_image)
    img = sel_buffer[:, :, 0:3]
    mask = sel_buffer[:, :, -1]
    process_size = 512

    mask_sum = mask.sum()
    if mask_sum >= WHITES:
        print("inpaiting with fixed Mask")
        mask = np.array(STATIC_MASK)[:, :, 0]
        img, mask = functbl[fill_mode](img, mask)
        init_image = Image.fromarray(img)
        mask = 255 - mask
        mask = skimage.measure.block_reduce(mask, (8, 8), np.max)
        mask = mask.repeat(8, axis=0).repeat(8, axis=1)
        mask_image = Image.fromarray(mask)
    elif mask_sum > 0 and mask_sum < WHITES:
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
    return output['images'][0], output["nsfw_content_detected"][0]


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
    proceed_button = gr.Button("Proceed", elem_id="proceed")
    model_output = gr.Image(label="Output")
    is_nsfw = gr.JSON()

    proceed_button.click(
        fn=run_outpaint,
        inputs=[
            model_input,
            sd_prompt,
            sd_strength,
            sd_guidance,
            sd_step,
            init_mode,
        ],
        outputs=[model_output, is_nsfw],
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


def get_room_count(room_id: str, jwtToken: str = ''):
    response = requests.get(
        f"https://liveblocks.net/api/v1/room/{room_id}/users", headers={"Authorization": f"Bearer {jwtToken}", "Content-Type": "application/json"})
    if response.status_code == 200:
        res = response.json()
        if "data" in res:
            return len(res["data"])
        else:
            return 0
    raise Exception("Error getting room count")


@app.on_event("startup")
@repeat_every(seconds=60)
async def sync_rooms():
    print("Syncing rooms")
    try:
        jwtToken = generateAuthToken()
        for db in get_db():
            rooms = db.execute("SELECT * FROM rooms").fetchall()
            for row in rooms:
                room_id = row["room_id"]
                users_count = get_room_count(room_id, jwtToken)
                cursor = db.cursor()
                cursor.execute(
                    "UPDATE rooms SET users_count = ? WHERE room_id = ?", (users_count, room_id))
                db.commit()
    except Exception as e:
        print(e)
        print("Rooms update failed")


@app.get('/api/rooms')
async def get_rooms(db: sqlite3.Connection = Depends(get_db)):
    rooms = db.execute("SELECT * FROM rooms").fetchall()
    return rooms


@app.post('/api/auth')
async def autorize(request: Request, db: sqlite3.Connection = Depends(get_db)):
    data = await request.json()
    room = data["room"]
    payload = {
        "userId": str(uuid.uuid4()),
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


@app.post('/api/uploadfile')
async def create_upload_file(background_tasks: BackgroundTasks, file: UploadFile):
    contents = await file.read()
    file_size = len(contents)
    if not 0 < file_size < 20E+06:
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
    s3.upload_fileobj(Fileobj=temp_file, Bucket=AWS_S3_BUCKET_NAME, Key="uploads/" +
                      file.filename, ExtraArgs={"ContentType": file.content_type, "CacheControl": "max-age=31536000"})
    temp_file.close()

    return {"url": f'https://d26smi9133w0oo.cloudfront.net/uploads/{file.filename}', "filename": file.filename}


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
