<script lang="ts">
	import { page } from '$app/stores';
	import Room from '$lib/Icons/Room.svelte';
	import Pin from '$lib/Icons/Pin.svelte';
	import People from '$lib/Icons/People.svelte';
	import LoadingIcon from '$lib/Icons/LoadingIcon.svelte';
	import { onMount } from 'svelte';
	import { selectedRoomID } from '$lib/store';
	import { MAX_CAPACITY } from '$lib/constants';
	import { useRooms } from '$lib/liveblocks';
	import type { RoomResponse } from '$lib/types';

	export let isLoading = false;
	let boxEl: HTMLElement;

	const rooms = useRooms();

	let collapsed = true;
	$: selectedRoom = $rooms.find((room) => room.room_id === $selectedRoomID);
	$: loadingRooms = $rooms.length > 0;

	function clickHandler(event: Event) {
		if (boxEl && !boxEl.contains(event.target as Node)) {
			collapsed = true;
		}
	}
	onMount(() => {
		window.addEventListener('pointerdown', clickHandler, true);
		return () => {
			window.removeEventListener('pointerdown', clickHandler, true);
		};
	});

	function changeRoom(room: RoomResponse) {
		$selectedRoomID = room.room_id;
		collapsed = true;
		$page.url.searchParams.set('roomid', room.room_id);
		window.location.search = `?${$page.url.searchParams.toString()}`;
		window.parent.postMessage({ queryString: `?${$page.url.searchParams.toString()}` }, '*');
	}
</script>

<!-- svelte-ignore a11y-click-events-have-key-events -->
<div class="min-w-[20ch]">
	{#if loadingRooms}
		<div
			class="text-sm rounded-2xl md:text-smtext-gray-700 py-1 font-medium tracking-tight relative ring-1 ring-blue-500 px-2"
			title="Choose a different room"
			bind:this={boxEl}
		>
			{#if !collapsed}
				<div
					class="absolute left-0 right-0 bottom-full rounded-xl bg-blue-600 px-1 overflow-hidden z-0"
				>
					<ul class="relative overflow-hidden overflow-y-scroll max-h-72 w-full x-scroll">
						<li class="grid-row gap-2 pb-2 sticky top-0 py-2 bg-blue-600 font-semibold">
							<Room />
							<span> room </span>
							<span />
							<People />
							<span> players </span>
						</li>
						{#each $rooms as room}
							<li>
								<!-- svelte-ignore a11y-invalid-attribute -->
								<a
									href="#"
									on:click|preventDefault={() => changeRoom(room)}
									class="grid-row gap-2 hover:bg-gray-300
						   {room.room_id === $selectedRoomID ? 'text-black' : ''}"
								>
									<span>
										{#if room.room_id === $selectedRoomID}
											<Pin />
										{/if}
									</span>
									<span>{room.room_id} </span>
									<span />
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
							{selectedRoom?.room_id}
						</span>
						<span />
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
	{:else}
		<div
			class="bg-gradient-to-r from-transparent via-blue-900/20 to-transparent py-1.5 text-blue-700 rounded-full flex justify-center items-center"
		>
			<LoadingIcon classList="animate-spin mr-2 text-sm" /> loading rooms
		</div>
	{/if}
</div>

<style lang="postcss" scoped>
	.grid-row {
		display: grid;
		grid-template-columns: 0.5fr 2fr 1fr 0.5fr 2fr;
		align-items: center;
		justify-items: flex-start;
	}
	.grid-row span {
		white-space: nowrap;
	}
</style>
