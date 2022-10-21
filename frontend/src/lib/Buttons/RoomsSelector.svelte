<script lang="ts">
	import { page } from '$app/stores';

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
		window.addEventListener('pointerdown', clickHandler, true);
		const interval = setInterval(refreshRooms, 3000);
		return () => {
			window.removeEventListener('pointerdown', clickHandler, true);
			clearInterval(interval);
		};
	});

	async function refreshRooms() {
		rooms = await fetch(PUBLIC_API_BASE + '/rooms').then((res) => res.json());
	}
	function changeRoom(room: RoomResponse) {
		$selectedRoomID = room.id;
		collapsed = true;
		$page.url.searchParams.set('roomid', room.room_id);
		window.location.search = `?${$page.url.searchParams.toString()}`;
	}
</script>

<!-- svelte-ignore a11y-click-events-have-key-events -->
<div class="min-w-[25ch]">
	{#if loadingRooms}
		<div
			class="text-xs rounded md:text-smtext-gray-700 py-1 font-medium tracking-tight relative z-0 
	{isLoading ? 'opacity-50' : ''}"
			title="Choose a different room"
			bind:this={boxEl}
		>
			{#if !collapsed}
				<div class="absolute left-0 right-0 bottom-full rounded-xl  bg-blue-600 px-1">
					<ul class="relative overflow-y-scroll max-h-72">
						<li class="grid-row gap-2 pb-3 sticky top-0 py-2">
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
									on:click|preventDefault={() => changeRoom(room)}
									class="grid-row gap-2 hover:bg-gray-300
						   {room.id === $selectedRoomID ? 'text-black' : ''}"
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
</div>

<style lang="postcss" scoped>
	.grid-row {
		display: grid;
		grid-template-columns: 0.5fr 2fr 0.5fr 2fr;
		align-items: center;
		justify-items: flex-start;
	}
</style>
