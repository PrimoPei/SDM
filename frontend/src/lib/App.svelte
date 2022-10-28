<script lang="ts">
	import Cursor from '$lib/Cursor.svelte';
	import Frame from '$lib/Frame.svelte';
	import PaintFrame from '$lib/PaintFrame.svelte';
	import PaintCanvas from '$lib/PaintCanvas.svelte';
	import Menu from '$lib/Menu.svelte';
	import PromptModal from '$lib/PromptModal.svelte';
	import { COLORS, FRAME_SIZE } from '$lib/constants';
	import { PUBLIC_WS_INPAINTING } from '$env/static/public';
	import type { PromptImgKey } from '$lib/types';
	import { Status } from '$lib/types';
	import {
		loadingState,
		currZoomTransform,
		maskEl,
		selectedRoomID,
		isRenderingCanvas
	} from '$lib/store';
	import { useMyPresence, useObject, useOthers } from '$lib/liveblocks';
	import { nanoid } from 'nanoid';

	const myPresence = useMyPresence({ addToHistory: true });
	const others = useOthers();
	let showModal = false;
	function getKey(position: { x: number; y: number }): PromptImgKey {
		return `${position.x}_${position.y}`;
	}

	const promptImgStorage = useObject('promptImgStorage');

	$: isLoading = $myPresence?.status === Status.loading || $isRenderingCanvas || false;
	function onShowModal(e: CustomEvent) {
		if (isLoading) return;
		showModal = e.detail.showModal;
		if (showModal) {
			myPresence.update({
				status: Status.prompting
			});
		} else {
			myPresence.update({
				status: Status.ready
			});
		}
	}

	function onPaint() {
		showModal = false;
		generateImage();
	}
	function canPaint(position: { x: number; y: number }): boolean {
		if (!$others) return true;
		let canPaint = true;
		for (const { presence } of $others) {
			if (
				position.x < presence.frame.x + FRAME_SIZE &&
				position.x + FRAME_SIZE > presence.frame.x &&
				position.y < presence.frame.y + FRAME_SIZE &&
				position.y + FRAME_SIZE > presence.frame.y
			) {
				// can paint if presence is only  dragging
				if (presence.status === Status.ready || presence.status === Status.dragging) {
					canPaint = true;
				}
				canPaint = false;
				break;
			}
		}
		return canPaint;
	}

	function clearStateMsg(t = 5000) {
		setTimeout(() => {
			$loadingState = '';
		}, t);
	}
	async function generateImage() {
		if (isLoading) return;
		const prompt = $myPresence.currentPrompt;
		const position = $myPresence.frame;
		$loadingState = 'Pending';
		if (!canPaint(position)) {
			$loadingState = 'Someone is already painting here';
			myPresence.update({
				status: Status.ready
			});
			clearStateMsg();
			return;
		}
		const imageKey = getKey(position);
		const room = $selectedRoomID || 'default';
		console.log('Generating...', prompt, position);
		myPresence.update({
			status: Status.loading
		});
		const sessionHash = crypto.randomUUID();
		const base64Crop = $maskEl.toDataURL('image/png');

		const hashpayload = {
			fn_index: 0,
			session_hash: sessionHash
		};

		const datapayload = {
			data: [base64Crop, prompt, 0.75, 7.5, 40, 'patchmatch', room, imageKey]
		};

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
					case 'send_hash':
						websocket.send(JSON.stringify(hashpayload));
						break;
					case 'send_data':
						$loadingState = 'Sending Data';
						websocket.send(JSON.stringify({ ...hashpayload, ...datapayload }));
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
							const params = data.output.data[0] as {
								is_nsfw: boolean;
								image: {
									url: string;
									filename: string;
								};
							};
							const isNSWF = params.is_nsfw;
							if (isNSWF) {
								throw new Error('NFSW');
							}
							// const imgBlob = await base64ToBlob(imgBase64);
							const promptImgParams = {
								prompt,
								imgURL: params.image.filename,
								position,
								date: new Date().getTime(),
								id: nanoid(),
								room: room
							};
							// const imgURL = await uploadImage(imgBlob, promptImgParams);

							$promptImgStorage.set(imageKey, promptImgParams);
							console.log(params.image.url);
							$loadingState = data.success ? 'Complete' : 'Error';
							clearStateMsg();
							myPresence.update({
								status: Status.ready,
								currentPrompt: ''
							});
						} catch (err) {
							const tError = err as Error;
							$loadingState = tError?.message;
							myPresence.update({
								status: Status.ready
							});
							clearStateMsg(10000);
						}
						websocket.close();
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
	<PromptModal
		on:paint={onPaint}
		initPrompt={$myPresence?.currentPrompt}
		on:showModal={onShowModal}
	/>
{/if}
<div class="fixed top-0 left-0 z-0 w-screen h-screen min-h-[600px]">
	<PaintCanvas />

	<main class="z-10 relative">
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
						color={COLORS[1 + (connectionId % (COLORS.length - 1))]}
						position={presence?.cursor}
						transform={$currZoomTransform}
					/>
				{/if}
			{/each}
		{/if}
		<PaintFrame transform={$currZoomTransform} on:showModal={onShowModal} />
	</main>
</div>
<div class="fixed bottom-0 md:bottom-16 left-0 right-0 z-10 my-2">
	<Menu {isLoading} on:showModal={onShowModal} />
</div>

<style lang="postcss" scoped>
</style>
