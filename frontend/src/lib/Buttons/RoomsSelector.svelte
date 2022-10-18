<script lang="ts">
	import Room from '$lib/Icons/Room.svelte';
	import Pin from '$lib/Icons/Pin.svelte';
	import People from '$lib/Icons/People.svelte';
	import { onMount } from 'svelte';
	import { PUBLIC_API_BASE } from '$env/static/public';
	import type { RoomResponse } from '$lib/types';
	import { selectedRoomID } from '$lib/store';
	import { MAX_CAPACITY } from '$lib/constants';
	export let isLoading = false;
	let boxEl: HTMLElement;

	let rooms: RoomResponse[] = [];

	let collapsed = true;
	$: selectedRoom = rooms.find((room) => room.id === $selectedRoomID);
	$: loadingRooms = rooms.length > 0;

	function clickHandler(event: Event) {
		if (!boxEl.contains(event.target as Node)) {
			collapsed = true;
		}
	}
	onMount(() => {
		refreshRooms();
		window.addEventListener('click', clickHandler, true);
		const interval = setInterval(refreshRooms, 3000);
		return () => {
			window.removeEventListener('click', clickHandler, true);
			clearInterval(interval);
		};
	});

	async function refreshRooms() {
		rooms = await fetch(PUBLIC_API_BASE + '/rooms').then((res) => res.json());
	}
</script>

<!-- svelte-ignore a11y-click-events-have-key-events -->
{#if loadingRooms}
	<div
		class="text-xs md:text-sm bg-violet-100 text-violet-900 px-3 py-1 font-mono font-medium tracking-tight relative z-0 min-w-[25ch] 
	{isLoading ? 'opacity-50' : ''}
	{collapsed ? 'rounded-xl' : 'rounded-b-xl'}"
		title="Choose a different room"
		bind:this={boxEl}
	>
		{#if !collapsed}
			<div class="absolute left-0 right-0 bottom-full rounded-t-xl bg-violet-100 px-1">
				<ul class="relative overflow-scroll max-h-72">
					<li class="grid-row gap-2 pb-3 sticky top-0 bg-violet-100 py-2">
						<Room />
						<span> room </span>
						<People />
						<span> players </span>
					</li>
					{#each rooms as room}
						<li>
							<!-- svelte-ignore a11y-invalid-attribute -->
							<a
								href="#"
								on:click|preventDefault={() => {
									$selectedRoomID = room.id;
									collapsed = true;
								}}
								class="grid-row gap-2 hover:bg-gray-300
						   {room.id === $selectedRoomID ? 'text-green-600' : ''}"
							>
								<span>
									{#if room.id === $selectedRoomID}
										<Pin />
									{/if}
								</span>
								<span>room {room.id} </span>
								<span />
								<span>{room.users_count} / {MAX_CAPACITY}</span>
							</a>
						</li>
					{/each}
				</ul>
				<div class="border-t-2 border-t-gray-400 border-opacity-50" />
			</div>
		{/if}
		<!-- svelte-ignore a11y-click-events-have-key-events -->
		<div
			class={isLoading ? 'cursor-wait' : 'cursor-pointer'}
			on:click={() => (isLoading ? null : (collapsed = !collapsed))}
		>
			{#if selectedRoom}
				<div class="grid-row gap-2">
					<Room />
					<span>
						room {selectedRoom?.id}
					</span>
					<People />
					<span>
						{selectedRoom?.users_count} / {MAX_CAPACITY}
					</span>
				</div>
			{:else}
				<div class="grid-row gap-2">
					<Room />
					<span>
						Loading...
						<People />
						<span> ... / ... </span>
					</span>
				</div>
			{/if}
		</div>
	</div>
{/if}

<style lang="postcss" scoped>
	.grid-row {
		display: grid;
		grid-template-columns: 0.5fr 2fr 0.5fr 2fr;
		align-items: center;
		justify-items: flex-start;
	}
</style>
