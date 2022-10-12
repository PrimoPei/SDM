<script lang="ts">
	import Move from '$lib/Icons/Move.svelte';
	export let isActive = false;
</script>

<button
	on:click
	class="bg-white rounded-full p-2 {isActive ? 'text-blue-700' : 'text-gray-800'}"
	title="Enable Dragging"
>
	<Move />
</button>

<style lang="postcss" scoped>
</style>
