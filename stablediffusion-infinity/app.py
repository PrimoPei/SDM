import io
import base64
import os
from random import sample
from sched import scheduler

import uvicorn
from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles

import httpx
from urllib.parse import urljoin


import numpy as np
import torch
from torch import autocast
from diffusers import StableDiffusionPipeline, StableDiffusionInpaintPipeline
from PIL import Image
from PIL import ImageOps
import gradio as gr
import base64
import skimage
import skimage.measure
from utils import *

app = FastAPI()

auth_token = os.environ.get("API_TOKEN") or True

WHITES = 66846720
MASK = Image.open("mask.png")
try:
    SAMPLING_MODE = Image.Resampling.LANCZOS
except Exception as e:
    SAMPLING_MODE = Image.LANCZOS


blocks = gr.Blocks().queue()
model = {}


def get_model():
    if "text2img" not in model:
        text2img = StableDiffusionPipeline.from_pretrained(
            "CompVis/stable-diffusion-v1-4",
            revision="fp16",
            torch_dtype=torch.float16,
            use_auth_token=auth_token,
        ).to("cuda")
        inpaint = StableDiffusionInpaintPipeline(
            vae=text2img.vae,
            text_encoder=text2img.text_encoder,
            tokenizer=text2img.tokenizer,
            unet=text2img.unet,
            scheduler=text2img.scheduler,
            safety_checker=text2img.safety_checker,
            feature_extractor=text2img.feature_extractor,
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
        model["text2img"] = text2img
        model["inpaint"] = inpaint
        # model["img2img"] = img2img

    return model["text2img"], model["inpaint"]
    # model["img2img"]


get_model()


def run_outpaint(
    input_image,
    prompt_text,
    strength,
    guidance,
    step,
    fill_mode,
):
    text2img, inpaint = get_model()
    sel_buffer = np.array(input_image)
    img = sel_buffer[:, :, 0:3]
    mask = sel_buffer[:, :, -1]
    process_size = 512

    mask_sum = mask.sum()
    if mask_sum >= WHITES:
        print("inpaiting with fixed Mask")
        mask = np.array(MASK)[:, :, 0]
        img, mask = functbl[fill_mode](img, mask)
        init_image = Image.fromarray(img)
        mask = 255 - mask
        mask = skimage.measure.block_reduce(mask, (8, 8), np.max)
        mask = mask.repeat(8, axis=0).repeat(8, axis=1)
        mask_image = Image.fromarray(mask)

        # mask_image=mask_image.filter(ImageFilter.GaussianBlur(radius = 8))
        with autocast("cuda"):
            images = inpaint(
                prompt=prompt_text,
                init_image=init_image.resize(
                    (process_size, process_size), resample=SAMPLING_MODE
                ),
                mask_image=mask_image.resize((process_size, process_size)),
                strength=strength,
                num_inference_steps=step,
                guidance_scale=guidance,
            )
    elif mask_sum > 0 and mask_sum < WHITES:
        print("inpainting")
        img, mask = functbl[fill_mode](img, mask)
        init_image = Image.fromarray(img)
        mask = 255 - mask
        mask = skimage.measure.block_reduce(mask, (8, 8), np.max)
        mask = mask.repeat(8, axis=0).repeat(8, axis=1)
        mask_image = Image.fromarray(mask)

        # mask_image=mask_image.filter(ImageFilter.GaussianBlur(radius = 8))
        with autocast("cuda"):
            images = inpaint(
                prompt=prompt_text,
                init_image=init_image.resize(
                    (process_size, process_size), resample=SAMPLING_MODE
                ),
                mask_image=mask_image.resize((process_size, process_size)),
                strength=strength,
                num_inference_steps=step,
                guidance_scale=guidance,
            )
    else:
        print("text2image")
        with autocast("cuda"):
            images = text2img(
                prompt=prompt_text, height=process_size, width=process_size,
            )

    return images['sample'][0], images["nsfw_content_detected"][0]


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

S3_HOST = "https://s3.amazonaws.com"


@app.get("/uploads/{path:path}")
async def uploads(path: str, response: Response):
    async with httpx.AsyncClient() as client:
        proxy = await client.get(f"{S3_HOST}/{path}")
    response.body = proxy.content
    response.status_code = proxy.status_code
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'POST, GET, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
    return response


app = gr.mount_gradio_app(app, blocks, "/gradio",
                          gradio_api_url="http://0.0.0.0:7860/gradio/")

app.mount("/", StaticFiles(directory="../static", html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860,
                log_level="debug", reload=False)
