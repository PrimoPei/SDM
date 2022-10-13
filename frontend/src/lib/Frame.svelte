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
	class="frame @apply absolute top-0 left-0 ring-8 ring-[#EC8E65] w-[512px] h-[512px]"
	style={`transform: translateX(${coord.x}px) translateY(${coord.y}px) scale(${transform.k}); transform-origin: 0 0;`}
>
	<div class="pointer-events-none touch-none">
		<div class="font-bold text-xl text-[#EC8E65] text-center px-2 line-clamp-4">{prompt}</div>
	</div>
	{#if isLoading}
		<div class="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
			<LoadingIcon />
		</div>
	{/if}
</div>

<style lang="postcss" scoped>
</style>
