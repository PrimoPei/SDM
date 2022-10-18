<script lang="ts">
	import Mask from '$lib/Icons/Mask.svelte';
	export let isActive = false;
	export let isLoading = false;
	export let className = '';
</script>

<button
	on:click
	disabled={isLoading}
	class="{className} rounded-full disabled:opacity-50  {isActive
		? 'text-blue-700'
		: 'text-gray-800'}"
	title="Draw to Mask"
>
	<Mask />
</button>

<style lang="postcss" scoped>
</style>
