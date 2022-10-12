<script lang="ts">
</script>

<button on:click class="button-paint bg-violet-100 text-violet-900" title="New Paint Frame">
	<span
		class="rounded-sm h-6 w-6 flex justify-center items-center border-2 border-dashed border-violet-700 mr-2"
	>
		+
	</span>
	<span>Prompt + Paint</span>
</button>

<style lang="postcss" scoped>
	/* .button {
		@apply disabled:opacity-50 dark:bg-white dark:text-black bg-black text-white rounded-2xl text-xs shadow-sm focus:outline-none focus:border-gray-400;
	} */
	.button-paint {
		@apply font-mono flex justify-center items-center disabled:opacity-50  dark:bg-white dark:text-black rounded-2xl px-3 py-1 shadow-sm focus:outline-none focus:border-gray-400;
	}
</style>
