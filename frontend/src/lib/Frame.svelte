<script lang="ts">
	import LoadingIcon from '$lib/Icons/LoadingIcon.svelte';
	import { FRAME_SIZE } from '$lib/constants';
	import type { ZoomTransform } from 'd3-zoom';
	import { Status } from '$lib/types';

	export let transform: ZoomTransform;
	export let position = { x: 0, y: 0 };
	export let prompt = '';
	export let status: Status;

	$: coord = {
		x: transform.applyX(position.x),
		y: transform.applyY(position.y)
	};
</script>

<div
	class="absolute top-0 left-0 border-8 border-dashed border-black flex items-center justify-center bg-black/60"
	style={`width: ${FRAME_SIZE}px;
			height: ${FRAME_SIZE}px;
			transform: translateX(${coord.x}px) translateY(${coord.y}px) scale(${transform.k}); transform-origin: 0 0;`}
>
	<div class="pointer-events-none touch-none">
		<div class="font-bold !text-4xl text-white rounded-2xl text-center p-10">
			{#if status === Status.loading || status === Status.processing}
				<LoadingIcon classList={'animate-spin text-4xl inline mr-2 mx-auto text-white mb-4'} />
				<p class="text-4xl">Someone is painting:</p>
			{:else if status === Status.masking}
				<p class="text-4xl">Someone is masking</p>
			{:else if status === Status.prompting}
				<p class="text-4xl">Someone is typing:</p>
			{/if}
			{#if prompt}
				<span class="italic font-normal line-clamp-4">"{prompt}"</span>
			{/if}
		</div>
	</div>
</div>
