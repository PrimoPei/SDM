<script lang="ts">
	import type { ZoomTransform } from 'd3-zoom';

	export let transform: ZoomTransform;
	export let color = '';
	export let emoji;
	export let position = { x: 0, y: 0 };

	$: coord = {
		x: transform.applyX(position.x),
		y: transform.applyY(position.y)
	};
</script>

<div
	class="cursor"
	style={`transform: translateX(${coord.x}px) translateY(${coord.y}px) scale(${transform.k});`}
>
	<svg
		class="block z-0 col-span-2 row-span-2"
		width="40"
		viewBox="0 0 15 15"
		fill="currentColor"
		xmlns="http://www.w3.org/2000/svg"
	>
		<path
			d="M0.91603 0.916054L7.09131 14.9234L8.89871 8.89873L14.9234 7.09133L0.91603 0.916054Z"
			fill="#FFB800"
		/>
	</svg>
	{#if emoji}
		<div
			class="absolute right-0 text-4xl col-start-2 row-start-2"
			style={`text-shadow: 0px 5px 5px ${color}`}
		>
			{emoji}
		</div>
	{/if}
</div>

<style lang="postcss" scoped>
	.cursor {
		@apply absolute top-0 left-0 grid grid-cols-3 touch-none pointer-events-none;
		transform-origin: 0 0;
	}
</style>
