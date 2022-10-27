<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import RoomsSelector from '$lib/Buttons/RoomsSelector.svelte';
	import AboutButton from '$lib/Buttons/AboutButton.svelte';
	import { toggleAbout } from '$lib/store';
	import ShareWithCommunity from '$lib/Buttons/ShareWithCommunity.svelte';
	// const broadcast = useBroadcastEvent();

	const dispatch = createEventDispatcher();

	export let isLoading = false;
</script>

<svelte:window
	on:keyup|preventDefault|stopPropagation={(e) => e.key === 'Enter' && dispatch('prompt')}
/>
<div class="flex flex-col md:flex-row items-center justify-between px-4 md:px-12 gap-3 md:gap-0">
	<div class="flex flex-col justify-center items-center">
		<AboutButton
			on:click={() => {
				$toggleAbout = !$toggleAbout;
			}}
		/>
		<div class="order-last max-w-[20ch]">
			<ShareWithCommunity />
		</div>
	</div>

	<button
		on:click={() => dispatch('prompt')}
		title="Click to prompt, and paint. The generated image will show up in the frame."
		disabled={isLoading}
		class="{isLoading
			? 'cursor-wait'
			: 'cursor-pointer'} order-first md:order-none text-xl md:text-3xl bg-blue-600 text-white px-6 py-2 rounded-2xl ring ring-blue-500 font-semibold shadow-2xl shadow-blue-500 self-center flex items-center hover:saturate-150"
		><span class="mr-3">🖍</span>Paint
		<span
			class="bg-blue-800 text-gray-300 rounded-lg px-2 py-0.5 text-base ml-4 hidden sm:flex items-center translate-y-[2px]"
			><svg
				class="text-sm mr-1.5"
				width="1em"
				height="1em"
				viewBox="0 0 10 13"
				fill="currentColor"
				xmlns="http://www.w3.org/2000/svg"
			>
				<path
					fill-rule="evenodd"
					clip-rule="evenodd"
					d="M8.5 8.5V0H9.5V9.5H1.70711L4.03553 11.8284C4.2308 12.0237 4.2308 12.3403 4.03553 12.5355C3.84027 12.7308 3.52369 12.7308 3.32843 12.5355L0.146447 9.35355C-0.0488155 9.15829 -0.0488155 8.84171 0.146447 8.64645L3.32843 5.46447C3.52369 5.2692 3.84027 5.2692 4.03553 5.46447C4.2308 5.65973 4.2308 5.97631 4.03553 6.17157L1.70711 8.5H8.5Z"
					fill="currentColor"
				/>
			</svg>
			Enter</span
		></button
	>

	<RoomsSelector {isLoading} />
	<!-- <PPButton {isLoading} on:click={() => dispatch('prompt')} /> -->
</div>
