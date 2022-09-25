<script lang="ts">
	import { currZoomTransform } from '$lib/store';
</script>

<div class="grid grid-cols-3 gap-3 text-sm w-max mx-auto">
	<div class="flex items-center">
		<input
			id="showframes"
			type="checkbox"
			class="w-4 h-4 text-blue-600 bg-gray-100 rounded border-gray-300 focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600 cursor-pointer"
		/>
		<label for="showframes" class="text-black dark:text-white cursor-pointer ml-2"
			>Show Frames</label
		>
	</div>
	<button class="button" title="Add Prompt"> Add Prompt </button>
	<button class="button-paint bg-violet-100 text-violet-900" title="New Paint Frame">
		<span
			class="rounded-sm h-5 w-5 m-1 flex justify-center items-center border-2 border-dashed border-violet-700 mr-2"
			>+</span
		>
		Paint
	</button>
</div>

<style lang="postcss" scoped>
	.link {
		@apply text-xs underline font-bold hover:no-underline hover:text-gray-500 visited:text-gray-500;
	}
	.input {
		@apply disabled:opacity-50 italic dark:placeholder:text-black placeholder:text-white text-white dark:text-black placeholder:text-opacity-30 dark:placeholder:text-opacity-10 dark:bg-white bg-slate-900 border-2 border-black rounded-2xl px-2 shadow-sm focus:outline-none focus:border-gray-400 focus:ring-1;
	}
	.button {
		@apply disabled:opacity-50 dark:bg-white dark:text-black bg-black text-white rounded-2xl text-xs shadow-sm focus:outline-none focus:border-gray-400;
	}
	.button-paint {
		@apply flex justify-center items-center disabled:opacity-50  dark:bg-white dark:text-black rounded-2xl shadow-sm focus:outline-none focus:border-gray-400;
	}
</style>
