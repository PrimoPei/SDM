<script lang="ts">
	import Cursor from '$lib/Cursor.svelte';
	import Frame from '$lib/Frame.svelte';
	import PaintFrame from '$lib/PaintFrame.svelte';
	import PaintCanvas from '$lib/PaintCanvas.svelte';
	import Menu from '$lib/Menu.svelte';
	import PromptModal from '$lib/PromptModal.svelte';
	import { COLORS, EMOJIS } from '$lib/constants';
	import { PUBLIC_WS_INPAINTING } from '$env/static/public';
	import type { PromptImgObject, PromptImgKey, Presence } from '$lib/types';
	import { Status } from '$lib/types';
	import { loadingState, currZoomTransform, maskEl } from '$lib/store';
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
		status: Status.dragging,
		currentPrompt: ''
	};
	myPresence.update(initialPresence);

	function getKey({ position }: PromptImgObject): PromptImgKey {
		return `${position.x}_${position.y}`;
	}

	const promptImgStorage = useObject('promptImgStorage');

	let showModal = false;

	$: isLoading = $myPresence?.status === Status.loading || false;

	function onPrompt() {
		if (!isLoading && !showModal) {
			showModal = true;
			myPresence.update({
				status: Status.prompting
			});
		}
	}
	function onClose() {
		showModal = false;
		console.log('close Modal');
	}

	function onPaint() {
		console.log('onPaint');
		generateImage();
		showModal = false;
	}

	async function generateImage() {
		if (isLoading) return;
		$loadingState = 'Pending';
		const prompt = $myPresence.currentPrompt;
		const position = $myPresence.frame;
		console.log('Generating...', prompt, position);
		myPresence.update({
			status: Status.loading
		});
		const sessionHash = crypto.randomUUID();
		const base64Crop = $maskEl.toDataURL('image/png');

		const payload = {
			fn_index: 0,
			data: [base64Crop, prompt, 0.75, 7.5, 40, 'patchmatch'],
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
					status: Status.ready
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
							status: Status.ready
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
							setTimeout(() => {
								$loadingState = '';
							}, 2000);
						} catch (err) {
							const tError = err as Error;
							$loadingState = tError?.message;
						}
						websocket.close();
						myPresence.update({
							status: Status.ready,
							currentPrompt: ''
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
	<PromptModal on:paint={onPaint} on:close={onClose} initPrompt={$myPresence?.currentPrompt} />
{/if}
<div class="fixed top-0 left-0 z-0 w-screen h-screen">
	<PaintCanvas />

	<main class="z-10 relative">
		<PaintFrame on:prompt={onPrompt} transform={$currZoomTransform} />

		<!-- When others connected, iterate through others and show their cursors -->
		{#if $others}
			{#each [...$others] as { connectionId, presence } (connectionId)}
				{#if (presence?.status === Status.loading || presence?.status === Status.prompting || presence?.status === Status.masking) && presence?.frame}
					<Frame
						isLoading={presence?.status === Status.loading}
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
	<Menu on:prompt={onPrompt} />
</div>

<style lang="postcss" scoped>
</style>
