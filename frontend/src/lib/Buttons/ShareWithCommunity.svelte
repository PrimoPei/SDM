<script lang="ts">
	import IconCommunity from '$lib/Icons/IconCommunity.svelte';
	import LoadingIcon from '$lib/Icons/LoadingIcon.svelte';
	import { uploadImage } from '$lib/utils';
	import { canvasEl, selectedRoomID } from '$lib/store';

	let isUploading: boolean = false;

	async function handleClick() {
		if (isUploading) {
			return;
		}
		const blob: Blob = await new Promise((resolve) => {
			$canvasEl.toBlob(resolve as BlobCallback, 'image/jpeg', 0.95);
		});
		isUploading = true;
		await createCommunityPost(blob);
		isUploading = false;
	}

	async function createCommunityPost(canvasBlob: Blob) {
		const canvasURL = await uploadImage(canvasBlob, 'canvas', 'canvas');
		const canvasImage = `<img src="${canvasURL.url}" style="width:100%" width="1000" height="1000">`;
		const descriptionMd = `#### Stable Diffusion Multiplayer:
		### Room ${$selectedRoomID}
<div style="display: flex; overflow: scroll; column-gap: 0.75rem;">
${canvasImage}
</div>`;

		const params = new URLSearchParams({
			title: `Room ${$selectedRoomID}`,
			description: descriptionMd
		});
		const paramsStr = params.toString();
		window.open(
			`https://huggingface.co/spaces/huggingface-projects/stable-diffusion-multiplayer/discussions/new?${paramsStr}`,
			'_blank'
		);
	}
</script>

<!-- svelte-ignore a11y-click-events-have-key-events -->
<div
	class="text-sm font-mono flex items-center justify-center bg-black gap-x-1 rounded-xl cursor-pointer px-2 py-1"
	on:click={handleClick}
	title="Share with community"
>
	{#if isUploading}
		<LoadingIcon classList={'animate-spin max-w-[25px]'} />
	{:else}
		<IconCommunity />
	{/if}
	<p class="text-white font-semibold">Share to community</p>
</div>
