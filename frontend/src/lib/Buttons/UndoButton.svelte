<script lang="ts">
	import Undo from '$lib/Icons/Undo.svelte';
	export let isActive = false;
	export let isLoading = false;
	export let className = '';
</script>

<button
	on:click
	disabled={isLoading}
	class="{className} bg-white rounded-full disabled:opacity-50 bg-white rounded-full {isActive
		? 'text-blue-700'
		: 'text-gray-800'}"
	title="Clear Masking"
>
	<Undo />
</button>

<style lang="postcss" scoped>
</style>
