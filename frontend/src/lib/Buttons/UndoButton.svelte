<script lang="ts">
	import Undo from '$lib/Icons/Undo.svelte';
	export let isActive = false;
</script>

<button
	on:click
	class="bg-white rounded-full p-2 {isActive ? 'text-blue-700' : 'text-gray-800'}"
	title="Clear Masking"
>
	<Undo />
</button>

<style lang="postcss" scoped>
</style>
