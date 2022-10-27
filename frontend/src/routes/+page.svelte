<script lang="ts">
	import { onMount } from 'svelte';
	import { createClient } from '@liveblocks/client';
	import type { Client } from '@liveblocks/client';
	import LiveblocksProvider from '$lib/liveblocks/LiveblocksProvider.svelte';
	import RoomProvider from '$lib/liveblocks/RoomProvider.svelte';
	import App from '$lib/App.svelte';
	import About from '$lib/About.svelte';
	import { PUBLIC_API_BASE } from '$env/static/public';
	import { selectedRoomID, toggleAbout } from '$lib/store';
	import type { RoomResponse } from '$lib/types';
	import { MAX_CAPACITY, CANVAS_SIZE, FRAME_SIZE } from '$lib/constants';
	import { Status } from '$lib/types';

	let loading = true;
	let client: Client;

	$: roomId = $selectedRoomID;

	onMount(() => {
		// document.addEventListener('wheel', (e) => e.preventDefault(), { passive: false });
		client = createClient({
			authEndpoint: PUBLIC_API_BASE + '/auth'
		});

		updateRooms();
	});

	async function updateRooms() {
		loading = true;
		const roomidParam = new URLSearchParams(window.location.search).get('roomid');
		const res = await fetch(PUBLIC_API_BASE + '/rooms');
		const rooms: RoomResponse[] = await res.json();
		const emptyRoom = rooms.find((room) => room.users_count < MAX_CAPACITY) || null;

		let roomAvailable = false;
		if (roomidParam) {
			const room = rooms.find((room) => room.room_id === roomidParam) || null;
			roomAvailable = room ? room.users_count < MAX_CAPACITY : false;
			if (room && roomAvailable) {
				$selectedRoomID = room.room_id;
				const state = { roomid: room.room_id };
				const queryString = '?' + new URLSearchParams(state).toString();
				window.history.replaceState(null, '', queryString);
				window.parent.postMessage({ queryString: queryString }, '*');
			}
		}
		if (emptyRoom && !roomAvailable) {
			selectedRoomID.set(emptyRoom.room_id);
			const state = { roomid: emptyRoom.room_id };
			const queryString = '?' + new URLSearchParams(state).toString();
			window.history.replaceState(null, '', queryString);
			window.parent.postMessage({ queryString: queryString }, '*');
		}
		loading = false;
		return { rooms };
	}
	const initialPresence = {
		cursor: null,
		frame: {
			x: CANVAS_SIZE.width / 2 - FRAME_SIZE / 2,
			y: CANVAS_SIZE.height / 2 - FRAME_SIZE / 2
		},
		status: Status.dragging,
		currentPrompt: ''
	};
</script>

<About classList={$toggleAbout ? 'flex' : 'hidden'} on:click={() => ($toggleAbout = false)} />

{#if loading}
	<div class="inset-0 fixed bg-white animate-pulse" />
{:else}
	<LiveblocksProvider {client}>
		{#if roomId}
			<RoomProvider id={roomId} {initialPresence}>
				<App />
			</RoomProvider>
		{:else}
			<div class="flex flex-col items-center justify-center h-full">
				<h1 class="text-2xl font-bold">No room selected</h1>
				<p class="text-gray-500">Please select a room in the URL</p>
			</div>
		{/if}
	</LiveblocksProvider>
{/if}
