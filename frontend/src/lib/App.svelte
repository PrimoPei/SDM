<script lang="ts">
	import Cursor from '$lib/Cursor.svelte';
	import Frame from '$lib/Frame.svelte';
	import PaintFrame from '$lib/PaintFrame.svelte';
	import Canvas from '$lib/Canvas.svelte';
	import Menu from '$lib/Menu.svelte';
	import PromptModal from '$lib/PromptModal.svelte';
	import { COLORS, EMOJIS } from '$lib/constants';
	import { PUBLIC_WS_INPAINTING } from '$env/static/public';
	import type { PromptImgObject, PromptImgKey, Presence } from '$lib/types';
	import { loadingState, currZoomTransform, showFrames } from '$lib/store';

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
	const initialPresence: Presence = {
		cursor: null,
		frame: null,
		isPrompting: false,
		isLoading: false,
		isMoving: true,
		currentPrompt: ''
	};
	myPresence.update(initialPresence);

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
	let showModal = false;
	let promptImgList: PromptImgObject[] = [];
	$: promptImgList = getpromptImgList($promptImgStorage?.toObject());

	$: isPrompting = $myPresence?.isPrompting || false;

	let canvasEl: HTMLCanvasElement;

	function onPaintMode(e: CustomEvent) {
		const mode = e.detail.mode;
		if (mode == 'paint' && !isPrompting) {
			showModal = true;
			myPresence.update({
				isPrompting: true
			});
		}
	}
	function onClose() {
		showModal = false;
	}

	function onPrompt(e: CustomEvent) {
		generateImage();
		showModal = false;
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
	async function generateImage() {
		if (isPrompting) return;
		$loadingState = 'Pending';
		const prompt = $myPresence.currentPrompt;
		const position = $myPresence.frame;
		console.log('Generating...', prompt, position);
		myPresence.update({
			isPrompting: true,
			isLoading: true
		});
		const sessionHash = crypto.randomUUID();
		const payload = {
			fn_index: 0,
			data: [getImageCrop(position), prompt, 0.75, 7.5, 30, 'patchmatch'],
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
				myPresence.update({
					isPrompting: false,
					isLoading: false
				});
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
						myPresence.update({
							isPrompting: false
						});
						return;
					case 'estimation':
						const { rank, queue_size } = data;
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
							const imgURL = await uploadImage(imgBlob, prompt);
							const promptImg = {
								prompt,
								imgURL: imgURL,
								position,
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
						myPresence.update({
							isPrompting: false
						});
						return;
					case 'process_starts':
						$loadingState = 'Processing';
						break;
				}
			} catch (e) {
				console.error(e);
				$loadingState = 'Error';
			}
		};
	}
</script>

<!-- Show the current user's cursor location -->
<div class="text touch-none pointer-events-none">
	{$loadingState}
</div>
{#if showModal}
	<PromptModal on:prompt={onPrompt} on:close={onClose} />
{/if}
<div class="fixed top-0 left-0 z-0 w-screen h-screen">
	<Canvas bind:value={canvasEl} />

	<main class="z-10 relative">
		<PaintFrame transform={$currZoomTransform} interactive={!isPrompting} />

		<!-- When others connected, iterate through others and show their cursors -->
		{#if $others}
			{#each [...$others] as { connectionId, presence } (connectionId)}
				{#if presence?.isPrompting && presence?.frame}
					<Frame
						color={COLORS[1 + (connectionId % (COLORS.length - 1))]}
						position={presence?.frame}
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
	<Menu on:paintMode={onPaintMode} />
</div>

<style lang="postcss" scoped>
</style>
