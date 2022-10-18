<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import IconCommunity from '$lib/Icons/IconCommunity.svelte';
	import LoadingIcon from '$lib/Icons/LoadingIcon.svelte';

	export let isUploading: boolean = false;

	const dispatch = createEventDispatcher();
	function handleClick() {
		if (isUploading) {
			return;
		}
		dispatch('createCommunityPost');
	}
</script>

<!-- svelte-ignore a11y-click-events-have-key-events -->
<div
	class="text-sm font-mono flex items-center justify-center bg-black gap-x-1 rounded-xl cursor-pointer px-2 py-1"
	on:click={handleClick}
	title="Share with community"
>
	{#if isUploading}
		<LoadingIcon classList="animate-spin max-w-[20px]" />
	{:else}
		<IconCommunity />
	{/if}
	<p class="text-white font-semibold">Share to community</p>
</div>
