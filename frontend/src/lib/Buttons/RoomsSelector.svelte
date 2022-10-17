<script lang="ts">
	import Room from '$lib/Icons/Room.svelte';
	import Pin from '$lib/Icons/Pin.svelte';
	import People from '$lib/Icons/People.svelte';
	import { onMount } from 'svelte';

	export let isLoading = false;
	let boxEl: HTMLElement;

	let rooms = Array(20)
		.fill(0)
		.map((_, i) => ({ label: `room ${i}`, total: ~~Math.random() * 20, capacity: 20 }));

	let selectedRoomID = 0;
	let collapsed = false;
	$: selectedRoom = rooms[selectedRoomID];

	function clickHandler(event: Event) {
		if (!boxEl.contains(event.target as Node)) {
			collapsed = true;
		}
	}
	onMount(() => {
		window.addEventListener('click', clickHandler, true);
		return () => {
			window.removeEventListener('click', clickHandler, true);
		};
	});
</script>

<!-- svelte-ignore a11y-click-events-have-key-events -->
<div
	class="text-xs md:text-sm bg-violet-100 text-violet-900 px-3 py-1 font-mono font-medium tracking-tight relative z-0 min-w-[25ch] 
	{isLoading ? 'opacity-50' : ''}
	{collapsed ? 'rounded-xl' : 'rounded-b-xl'}"
	bind:this={boxEl}
>
	{#if !collapsed}
		<div
			class="absolute z-20 left-0 right-0 bottom-full rounded-t-xl bg-violet-100 px-1 overflow-y-scroll max-h-80"
		>
			<ul class="relative">
				<li class="grid-row gap-2 pb-3 sticky top-0 bg-violet-100 py-2">
					<Room />
					<span> room </span>
					<People />
					<span> players </span>
				</li>
				{#each rooms as room, i}
					<li>
						<!-- svelte-ignore a11y-invalid-attribute -->
						<a
							href="#"
							on:click|preventDefault={() => {
								selectedRoomID = i;
								collapsed = true;
							}}
							class="grid-row gap-2 hover:bg-gray-300
						   {i === selectedRoomID ? 'text-green-600' : ''}"
						>
							<span>
								{#if i === selectedRoomID}
									<Pin />
								{/if}
							</span>
							<span> {room.label} </span>
							<span />
							<span>{room.total} / {room.capacity}</span>
						</a>
					</li>
				{/each}
			</ul>
			<div class="border-t-2 border-t-gray-400 border-opacity-50" />
		</div>
	{/if}
	<!-- svelte-ignore a11y-click-events-have-key-events -->
	<div
		class="grid-row gap-2 relative
		{isLoading ? 'cursor-wait' : 'cursor-pointer'}"
		on:click={() => (isLoading ? null : (collapsed = !collapsed))}
	>
		<Room />
		<span> {selectedRoom.label} </span>
		<People />
		<span> {selectedRoom.total} / {selectedRoom.capacity} </span>
	</div>
</div>

<style lang="postcss" scoped>
	.grid-row {
		display: grid;
		grid-template-columns: 0.5fr 2fr 0.5fr 2fr;
		align-items: center;
		justify-items: flex-start;
	}
</style>
