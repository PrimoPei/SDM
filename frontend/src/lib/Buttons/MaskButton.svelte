<script lang="ts">
	import Mask from '$lib/Icons/Mask.svelte';
	export let isActive = false;
	export let isLoading = false;
	export let className = '';
</script>

<button
	on:click
	disabled={isLoading}
	class="{className} rounded-full disabled:opacity-50  {isActive ? 'text-white' : 'text-blue-200'}"
	title="Draw to Mask"
>
	<Mask classList="text-3xl" />
</button>

<style lang="postcss" scoped>
</style>
