<script lang="ts">
	import LiveBlocks from '$lib/Icons/LiveBlocks.svelte';
	export let classList = '';
</script>

<!-- svelte-ignore a11y-click-events-have-key-events -->
<div
	on:click
	class="fixed {classList} w-screen h-screen top-0 left-0 bottom-0 right-0 z-50 items-center justify-center bg-black text-white bg-opacity-90 px-3"
>
	<div class="max-w-md">
		<h2 class="font-bold text-xl font-mono mb-8">Stable Difussion Multiplayer</h2>
		<ul>
			<li class="mb-2">
				Powered by <a
					href="https://huggingface.co/docs/hub/spaces-gpus"
					class="text-blue-400 hover:text-blue-600 underline"
					>Hugging Face GPU Spaces
				</a>
			</li>
			<li class="mb-2">
				<a
					href="https://huggingface.co/docs/diffusers/index"
					class="text-blue-400 hover:text-blue-600 underline"
				>
					Diffusers
				</a>
				and
				<a
					href="https://github.com/runwayml/stable-diffusion"
					target="_blank"
					class="text-blue-400 hover:text-blue-600 underline"
					rel="noopener noreferrer"
				>
					Runwayml Inpaiting Stable Diffusion</a
				>
			</li>
			<li class="mb-2">
				Thanks to <a
					href="https://twitter.com/lkwq007"
					target="_blank"
					rel="noopener noreferrer"
					class="text-blue-400 hover:text-blue-600 underline"
				>
					Lnyan</a
				>
				for the original outpainting technique implemented on
				<a
					href="https://github.com/lkwq007/stablediffusion-infinity"
					target="_blank"
					rel="noopener noreferrer"
					class="text-blue-400 hover:text-blue-600 underline"
					>Stable Diffusion Infinity
				</a>
			</li>

			<li class="mb-2">
				<p class="text-base flex items-center">
					Multiplayer API by
					<LiveBlocks classList="ml-2" />
				</p>
			</li>
		</ul>
	</div>
</div>
