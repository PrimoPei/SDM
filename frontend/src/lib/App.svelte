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
	import type { PromptImgObject, PromptImgKey } from '$lib/types';
	import {
		isLoading,
		loadingState,
		currZoomTransform,
		isPrompting,
		clickedPosition,
		showFrames
	} from '$lib/store';

	import { useMyPresence, useObject, useOthers } from '$lib/liveblocks';

	import { base64ToBlob, uploadImage } from '$lib/utils';

	import { nanoid } from 'nanoid';

	/**
	 * The main Liveblocks code for the example.
	 * Check in src/routes/index.svelte to see the setup code.
	 */

	const myPresence = useMyPresence();
	const others = useOthers();

	// Set a default value for presence
	myPresence.update({
		name: '',
		cursor: null,
		isPrompting: false,
		currentPrompt: ''
	});
	$: {
		console.log($others)
	}
	function getKey({ position }: PromptImgObject): PromptImgKey {
		return `${position.x}_${position.y}`;
	}

	const promptImgStorage = useObject('promptImgStorage');

	function getpromptImgList(promptImgList: PromptImgObject[]): PromptImgObject[] {
		if (promptImgList) {
			const list: PromptImgObject[] = Object.values(promptImgList);
			return list.sort((a, b) => a.date - b.date);
		}
		return [];
	}
	let promptImgList: PromptImgObject[] = [];
	$: promptImgList = getpromptImgList($promptImgStorage?.toObject());

	let canvasEl: HTMLCanvasElement;

	async function onClose(e: CustomEvent) {
		$isPrompting = false;
	}
	async function onPrompt(e: CustomEvent) {
		const prompt = e.detail.prompt;
		const imgURLs = await generateImage(prompt);
		$isPrompting = false;
		console.log('prompt', prompt, imgURLs);
	}
	function getImageCrop(cursor: { x: number; y: number }) {
		const canvasCrop = document.createElement('canvas');

		canvasCrop.width = 512;
		canvasCrop.height = 512;

		const ctxCrop = canvasCrop.getContext('2d') as CanvasRenderingContext2D;

		// crop image from point canvas
		ctxCrop.save();
		ctxCrop.clearRect(0, 0, 512, 512);
		ctxCrop.globalCompositeOperation = 'source-over';
		ctxCrop.drawImage(canvasEl, cursor.x, cursor.y, 512, 512, 0, 0, 512, 512);
		ctxCrop.restore();

		const base64Crop = canvasCrop.toDataURL('image/png');

		return base64Crop;
	}
	async function generateImage(_prompt: string) {
		if (!_prompt || $isLoading == true) return;
		$loadingState = 'Pending';
		$isLoading = true;
		myPresence.update({
			currentPrompt: _prompt,
			isPrompting: true,
			cursor: $clickedPosition
		});
		const sessionHash = crypto.randomUUID();
		const payload = {
			fn_index: 0,
			data: [getImageCrop($clickedPosition), _prompt, 0.75, 7.5, 30, 'patchmatch'],
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
							if (isNSWF) {
								throw new Error('Potential NFSW content, please try again');
							}
							const imgBlob = await base64ToBlob(imgBase64);
							const imgURL = await uploadImage(imgBlob, _prompt);
							const promptImg = {
								prompt: _prompt,
								imgURL: imgURL,
								position: $clickedPosition,
								date: new Date().getTime(),
								id: nanoid()
							};
							const key = getKey(promptImg);
							$promptImgStorage.set(key, promptImg);
							console.log(imgURL);
							$loadingState = data.success ? 'Complete' : 'Error';
						} catch (err) {
							const tError = err as Error;
							$loadingState = tError?.message;
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
	let currentPrompt = '';
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
		{#if promptImgList && $showFrames}
			{#each promptImgList as promptImg, i}
				<Frame
					color={COLORS[0]}
					transform={$currZoomTransform}
					position={promptImg?.position}
					prompt={promptImg?.prompt}
				/>
			{/each}
		{/if}
		<!-- {#if $clickedPosition}
			<Frame color={COLORS[0]} position={$clickedPosition} transform={$currZoomTransform} />
		{/if} -->
		{#if $myPresence?.cursor}
			<!-- <Frame color={COLORS[0]} position={$myPresence.cursor} transform={$currZoomTransform} /> -->
			<Cursor
				emoji={EMOJIS[0]}
				color={COLORS[0]}
				position={$myPresence.cursor}
				transform={$currZoomTransform}
			/>
		{/if}

		<!-- When others connected, iterate through others and show their cursors -->
		{#if $others}
			{#each [...$others] as { connectionId, presence } (connectionId)}
				{#if presence?.isPrompting && presence?.cursor}
					<Frame
						color={COLORS[1 + (connectionId % (COLORS.length - 1))]}
						position={presence?.cursor}
						prompt={presence?.currentPrompt}
						transform={$currZoomTransform}
					/>
				{/if}
				{#if presence?.cursor}
					<Cursor
						emoji={EMOJIS[1 + (connectionId % (EMOJIS.length - 1))]}
						color={COLORS[1 + (connectionId % (COLORS.length - 1))]}
						position={presence?.cursor}
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
