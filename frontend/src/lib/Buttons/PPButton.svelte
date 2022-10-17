<script lang="ts">
	export let isLoading = false;
</script>

<button
	on:click
	disabled={isLoading}
	class="button-paint"
	title="New Paint Frame"
>
	{#if isLoading}
		<span>paiting... </span>{:else}
		<span
			class="rounded-sm h-6 w-6 flex justify-center items-center border-2 border-dashed border-violet-700 mr-2"
		>
			+
		</span>
		<span>Prompt + Paint</span>
	{/if}
</button>

<style lang="postcss" scoped>
	/* .button {
		@apply disabled:opacity-50 dark:bg-white dark:text-black bg-black text-white rounded-2xl text-xs shadow-sm focus:outline-none focus:border-gray-400;
	} */
	.button-paint {
		@apply text-sm font-mono bg-violet-100 text-violet-900 min-w-[25ch] flex justify-center items-center disabled:opacity-50 dark:bg-white dark:text-black rounded-2xl px-3 py-1 shadow-sm focus:outline-none focus:border-gray-400;
	}
</style>
