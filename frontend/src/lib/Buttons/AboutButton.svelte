<button on:click class="button-paint" title="Prompt and Paint">
	<span>About</span>
</button>

<style lang="postcss" scoped>
	/* .button {
		@apply disabled:opacity-50 dark:bg-white dark:text-black bg-black text-white rounded-2xl text-xs shadow-sm focus:outline-none focus:border-gray-400;
	} */
	.button-paint {
		@apply text-xs md:text-sm font-mono bg-blue-100 text-blue-900 min-w-[25ch] flex justify-center items-center disabled:opacity-50 rounded-xl px-3 py-1 shadow-sm focus:outline-none focus:border-gray-400;
	}
</style>
