<script lang="ts">
	import LiveBlocks from '$lib/Icons/LiveBlocks.svelte';
	export let classList = '';
</script>

<!-- svelte-ignore a11y-click-events-have-key-events -->
<div
	on:click
	class="fixed {classList} w-screen h-screen top-0 left-0 bottom-0 right-0 z-50 items-center justify-center bg-black text-white bg-opacity-90 px-3 overflow-y-scroll"
>
	<div class="max-w-md">
		<h2 class="font-bold text-xl font-mono mb-8">Stable Difussion Multiplayer</h2>
		<p>
			Powered by Hugging Face face GPU Spaces <a
				href="https://huggingface.co/docs/hub/spaces-gpus"
				class="text-blue-400 hover:text-blue-600 underline"
				>https://huggingface.co/docs/hub/spaces-gpus</a
			>
			Diffusers
			<a
				href="https://huggingface.co/docs/diffusers/index"
				class="text-blue-400 hover:text-blue-600 underline"
				>https://huggingface.co/docs/diffusers/index</a
			>
		</p>
		<p>
			Thanks to <a
				href="https://twitter.com/lkwq007"
				target="_blank"
				rel="noopener noreferrer"
				class="text-blue-400 hover:text-blue-600 underline"
			>
				Lnyan</a
			>
			for the original outpaiting technique implemented on
			<a
				href="https://github.com/lkwq007/stablediffusion-infinity"
				target="_blank"
				rel="noopener noreferrer"
				class="text-blue-400 hover:text-blue-600 underline"
				>Stable Diffusion Infinity
			</a>.
		</p>
		<p class="mb-6">
			Runwayml Inpaiting Stable Diffusion
			<a
				href="https://github.com/runwayml/stable-diffusion"
				target="_blank"
				rel="noopener noreferrer"
			>
				https://github.com/runwayml/stable-diffusion</a
			>
		</p>
		<p class="text-base flex items-center">
			Multiplayer API by
			<LiveBlocks classList="ml-2" />
		</p>
	</div>
</div>
