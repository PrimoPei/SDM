<script lang="ts">
	import Cursor from '$lib/Cursor.svelte';
	import Frame from '$lib/Frame.svelte';
	import Canvas from '$lib/Canvas.svelte';
	import Menu from '$lib/Menu.svelte';
	import PromptModal from '$lib/PromptModal.svelte';
	import type { Room } from '@liveblocks/client';
	import { COLORS, EMOJIS } from '$lib/constants';
	import { PUBLIC_WS_INPAINTING } from '$env/static/public';
	import { onMount } from 'svelte';
	import {
		isLoading,
		loadingState,
		currZoomTransform,
		myPresence,
		others,
		isPrompting,
		clickedPosition,
		imagesList,
		showFrames,
		text2img
	} from '$lib/store';
	import { base64ToBlob, uploadImage } from '$lib/utils';
	/**
	 * The main Liveblocks code for the example.
	 * Check in src/routes/index.svelte to see the setup code.
	 */

	export let room: Room;

	let canvasEl: HTMLCanvasElement;

	onMount(() => {});

	async function onClose(e: CustomEvent) {
		$isPrompting = false;
	}
	async function onPrompt(e: CustomEvent) {
		const prompt = e.detail.prompt;
		const imgURLs = await generateImage(prompt);
		$isPrompting = false;
		console.log('prompt', prompt, imgURLs);
	}
	function getImageMask(cursor: { x: number; y: number }) {
		const tempCanvas = document.createElement('canvas');
		const canvasCrop = document.createElement('canvas');
		const mask = document.createElement('canvas');

		tempCanvas.width = 512;
		tempCanvas.height = 512;
		canvasCrop.width = 512;
		canvasCrop.height = 512;
		mask.width = 512;
		mask.height = 512;

		const tempCanvasCtx = tempCanvas.getContext('2d') as CanvasRenderingContext2D;
		const ctxCrop = canvasCrop.getContext('2d') as CanvasRenderingContext2D;
		const ctxMask = mask.getContext('2d') as CanvasRenderingContext2D;

		// crop image from point canvas
		ctxCrop.save();
		ctxCrop.clearRect(0, 0, 512, 512);

	
		ctxCrop.globalCompositeOperation = 'source-over';
		ctxCrop.drawImage(canvasEl, cursor.x, cursor.y, 512, 512, 0, 0, 512, 512);
		ctxCrop.restore();

		// create black image
		tempCanvasCtx.fillStyle = 'black';
		tempCanvasCtx.fillRect(0, 0, 512, 512);

		// create Mask
		ctxMask.save();
		// ctxMask.clearRect(0, 0, 512, 512);
		ctxMask.drawImage(canvasCrop, 0, 0, 512, 512);
		ctxMask.globalCompositeOperation = 'source-in';
		ctxMask.drawImage(tempCanvas, 0, 0);
		ctxMask.restore();

		tempCanvasCtx.fillStyle = 'white';
		tempCanvasCtx.fillRect(0, 0, 512, 512);
		//random pixels
		// const imageData = tempCanvasCtx.getImageData(0, 0, 512, 512);
		// const pix = imageData.data;
		// for (let i = 0, n = pix.length; i < n; i += 4) {
		// 	pix[i] = Math.round(255 * Math.random());
		// 	pix[i + 1] = Math.round(255 * Math.random());
		// 	pix[i + 2] = Math.round(255 * Math.random());
		// 	pix[i + 3] = 255;
		// }
		// tempCanvasCtx.putImageData(imageData, 0, 0);
		tempCanvasCtx.drawImage(canvasCrop, 0, 0, 512, 512);
		//convert canvas to base64
		const base64Crop = tempCanvas.toDataURL('image/png');
	
		tempCanvasCtx.fillStyle = 'white';
		tempCanvasCtx.fillRect(0, 0, 512, 512);
		tempCanvasCtx.drawImage(mask, 0, 0, 512, 512);
		//convert canvas to base64
		const base64Mask = tempCanvas.toDataURL('image/png');
		
		return { image: base64Crop, mask: base64Mask };
	}

	async function generateImage(_prompt: string) {
		// getImageMask($clickedPosition);
		// return;
		if (!_prompt || $isLoading == true) return;
		$loadingState = 'Pending';
		$isLoading = true;
		const sessionHash = crypto.randomUUID();
		const payload = {
			fn_index: 0,
			data: [
				$text2img ? null : getImageMask($clickedPosition),
				// { mask: null, image: null },
				_prompt,
				$text2img
			],
			session_hash: sessionHash
		};
		console.log('payload', payload);

		const websocket = new WebSocket(PUBLIC_WS_INPAINTING);
		// websocket.onopen = async function (event) {
		// 	websocket.send(JSON.stringify({ hash: sessionHash }));
		// };
		websocket.onclose = (evt) => {
			if (!evt.wasClean) {
				$loadingState = 'Error';
				$isLoading = false;
			}
		};
		websocket.onmessage = async function (event) {
			try {
				const data = JSON.parse(event.data);
				$loadingState = '';
				switch (data.msg) {
					case 'send_data':
						$loadingState = 'Sending Data';
						websocket.send(JSON.stringify(payload));
						break;
					case 'queue_full':
						$loadingState = 'Queue full';
						websocket.close();
						$isLoading = false;
						return;
					case 'estimation':
						const { msg, rank, queue_size } = data;
						$loadingState = `On queue ${rank}/${queue_size}`;
						break;
					case 'process_generating':
						$loadingState = data.success ? 'Generating' : 'Error';
						break;
					case 'process_completed':
						try {
							const imgBase64 = data.output.data[0] as string;
							const isNSWF = data.output.data[1] as boolean;

							const imgBlob = await base64ToBlob(imgBase64);
							const imgURL = await uploadImage(imgBlob, _prompt);

							$imagesList.push({
								prompt: _prompt,
								imgURL: imgURL,
								position: $clickedPosition
							});
							console.log(imgURL);
							$loadingState = data.success ? 'Complete' : 'Error';
						} catch (e) {
							$loadingState = e.message;
						}
						websocket.close();
						$isLoading = false;
						return;
					case 'process_starts':
						$loadingState = 'Processing';
						break;
				}
			} catch (e) {
				console.error(e);
				$isLoading = false;
				$loadingState = 'Error';
			}
		};
	}
	let modal = false;
</script>

<!-- Show the current user's cursor location -->
<div class="text touch-none pointer-events-none">
	{$loadingState}
	{$isLoading}
</div>
{#if $isPrompting}
	<PromptModal on:prompt={onPrompt} on:close={onClose} />
{/if}
<div class="fixed top-0 left-0 z-0 w-screen h-screen">
	<Canvas bind:value={canvasEl} />

	<main class="z-10 relative">
		{#if $imagesList && $showFrames}
			{#each $imagesList as image, i}
				<Frame
					color={COLORS[0]}
					position={$imagesList.get(i).position}
					transform={$currZoomTransform}
				/>
			{/each}
		{/if}
		{#if $clickedPosition}
			<Frame color={COLORS[0]} position={$clickedPosition} transform={$currZoomTransform} />
		{/if}
		{#if $myPresence?.cursor}
			<Frame color={COLORS[0]} position={$myPresence.cursor} transform={$currZoomTransform} />
			<Cursor
				emoji={EMOJIS[0]}
				color={COLORS[0]}
				position={$myPresence.cursor}
				transform={$currZoomTransform}
			/>
		{/if}

		<!-- When others connected, iterate through others and show their cursors -->
		{#if others}
			{#each [...$others] as { connectionId, presence } (connectionId)}
				{#if presence?.cursor}
					<Frame
						color={COLORS[1 + (connectionId % (COLORS.length - 1))]}
						position={presence.cursor}
						transform={$currZoomTransform}
					/>

					<Cursor
						emoji={EMOJIS[1 + (connectionId % (EMOJIS.length - 1))]}
						color={COLORS[1 + (connectionId % (COLORS.length - 1))]}
						position={presence.cursor}
						transform={$currZoomTransform}
					/>
				{/if}
			{/each}
		{/if}
	</main>
</div>

<div class="fixed bottom-0 left-0 right-0 z-10 my-2">
	<Menu />
</div>

<style lang="postcss" scoped>
</style>
