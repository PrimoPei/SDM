<script lang="ts">
	import { spring } from 'svelte/motion';

	export let color = '';
	export let emoji = '';
	export let x = 0;
	export let y = 0;

	// Spring animation for cursor
	const coords = spring(
		{ x, y },
		{
			stiffness: 0.07,
			damping: 0.35
		}
	);
	// Update spring when x and y change
	$: coords.set({ x, y });
</script>

<div
	class="absolute top-0 left-0 grid grid-cols-3"
	style={`transform: translateX(${$coords.x}px) translateY(${$coords.y}px);`}
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
	<div
		class="absolute right-0 text-4xl col-start-2 row-start-2"
		style={`text-shadow: 0px 5px 5px ${color}`}
	>
		{emoji}
	</div>
</div>

<style lang="postcss" scoped>
</style>
