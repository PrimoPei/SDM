<script lang="ts">
	import LoadingIcon from '$lib/Icons/LoadingIcon.svelte';

	import type { ZoomTransform } from 'd3-zoom';

	export let transform: ZoomTransform;
	export let position = { x: 0, y: 0 };
	export let prompt = '';
	export let isLoading = false;
	$: coord = {
		x: transform.applyX(position.x),
		y: transform.applyY(position.y)
	};
</script>

<div
	class="frame absolute top-0 left-0 ring-8 ring-black w-[512px] h-[512px] flex items-center justify-center bg-black/60"
	style={`transform: translateX(${coord.x}px) translateY(${coord.y}px) scale(${transform.k}); transform-origin: 0 0;`}
>
	<div class="pointer-events-none touch-none">
		{#if isLoading}
			<LoadingIcon classList={'animate-spin text-4xl inline mr-2 mx-auto text-white mb-4'} />
		{/if}
		<div
			class="font-bold !text-4xl text-white bg-black/60 rounded-2xl text-center p-10 line-clamp-4 flex"
		>
			<p class="text-4xl">Someone is painting:</p>

			<span class="italic font-normal">"{prompt}"</span>
		</div>
	</div>
</div>
