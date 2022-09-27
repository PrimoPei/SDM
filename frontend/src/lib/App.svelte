<script lang="ts">
	import Cursor from '$lib/Cursor.svelte';
	import Frame from '$lib/Frame.svelte';
	import Canvas from '$lib/Canvas.svelte';
	import Menu from '$lib/Menu.svelte';
	import PromptModal from '$lib/PromptModal.svelte';
	import type { Room } from '@liveblocks/client';
	import { COLORS, EMOJIS } from '$lib/constants';
	import { PUBLIC_WS_ENDPOINT } from '$env/static/public';
	import { onMount } from 'svelte';
	import {
		isLoading,
		loadingState,
		currZoomTransform,
		myPresence,
		others,
		isPrompting,
		clickedPosition,
		imagesList
	} from '$lib/store';
	import { base64ToBlob, uploadImage } from '$lib/utils';
	/**
	 * The main Liveblocks code for the example.
	 * Check in src/routes/index.svelte to see the setup code.
	 */

	export let room: Room;
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
	async function generateImage(_prompt: string) {
		if (!_prompt || $isLoading == true) return;
		$loadingState = 'Pending';
		$isLoading = true;
		const sessionHash = crypto.randomUUID();

		const payload = {
			fn_index: 2,
			data: [_prompt],
			session_hash: sessionHash
		};
		const websocket = new WebSocket(PUBLIC_WS_ENDPOINT);
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
							const imgsBase64 = data.output.data[0] as string[];
							const imgBlobs = await Promise.all(imgsBase64.map((base64) => base64ToBlob(base64)));
							const imgURLs = await Promise.all(imgBlobs.map((blob) => uploadImage(blob, _prompt)));
							$imagesList.push({
								prompt: _prompt,
								images: imgURLs,
								position: $clickedPosition
							});
							console.log(imgURLs);
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
<div class="text">
	{$myPresence?.cursor
		? `${$myPresence.cursor.x} × ${$myPresence.cursor.y}`
		: 'Move your cursor to broadcast its position to other people in the room.'}
	{$loadingState}
	{$isLoading}
</div>
{#if $isPrompting}
	<PromptModal on:prompt={onPrompt} on:close={onClose} />
{/if}
<div class="fixed top-0 left-0 z-0 w-screen h-screen cursor-none">
	<Canvas />

	<main class="z-10 relative">
		{#if $imagesList}
			{#each $imagesList as image, i}
				<Frame
					color={COLORS[0]}
					position={$imagesList.get(i).position}
					images={$imagesList.get(i).images}
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
