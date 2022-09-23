<script lang="ts">
	import { isLoading, loadingState } from '$lib/store';
	import { PUBLIC_WS_ENDPOINT, PUBLIC_DEV_MODE } from '$env/static/public';

	const apiUrl =
		PUBLIC_DEV_MODE === 'DEV'
			? 'http://localhost:7860'
			: '/embed/huggingface-projects/color-palette-generator-sd';
</script>

<div class="max-w-screen-md mx-auto px-3 py-8 relative z-0">
	<h1 class="text-3xl font-bold leading-normal">Stable Diffussion Outpainting Multiplayer</h1>
	<p class="text-sm" />
	<div class="relative top-0 z-50 bg-white dark:bg-black py-3">
		<form class="grid grid-cols-6">
			<input
				class="input"
				placeholder="A photo of a beautiful sunset in San Francisco"
				title="Input prompt to generate image and obtain palette"
				type="text"
				name="prompt"
				disabled={$isLoading}
			/>
			<button class="button" disabled={$isLoading} title="Generate Palette">
				Create Palette
			</button>
		</form>
	</div>
</div>

<style lang="postcss" scoped>
	.link {
		@apply text-xs underline font-bold hover:no-underline hover:text-gray-500 visited:text-gray-500;
	}
	.input {
		@apply text-sm disabled:opacity-50 col-span-4 md:col-span-5 italic dark:placeholder:text-black placeholder:text-white text-white dark:text-black placeholder:text-opacity-30 dark:placeholder:text-opacity-10 dark:bg-white bg-slate-900 border-2 border-black rounded-2xl px-2 shadow-sm focus:outline-none focus:border-gray-400 focus:ring-1;
	}
	.button {
		@apply disabled:opacity-50 col-span-2 md:col-span-1 dark:bg-white dark:text-black border-2 border-black rounded-2xl ml-2 px-2 py-2  text-xs shadow-sm font-bold focus:outline-none focus:border-gray-400;
	}
</style>
