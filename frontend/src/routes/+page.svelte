<script lang="ts">
	import { onMount } from 'svelte';
	import { createClient } from '@liveblocks/client';
	import type { Client } from '@liveblocks/client';
	import LiveblocksProvider from '$lib/liveblocks/LiveblocksProvider.svelte';
	import RoomProvider from '$lib/liveblocks/RoomProvider.svelte';
	import ContentWarningModal from '$lib/ContentWarningModal.svelte';
	import App from '$lib/App.svelte';
	import About from '$lib/About.svelte';
	import { PUBLIC_API_BASE } from '$env/static/public';
	import { selectedRoomID, toggleAbout, canvasSize } from '$lib/store';
	import type { RoomResponse } from '$lib/types';
	import { MAX_CAPACITY, FRAME_SIZE } from '$lib/constants';
	import { Status } from '$lib/types';
	import Cookies from 'js-cookie';

	let loading = true;
	let client: Client;
	let hideContentModal = true;

	$: roomId = $selectedRoomID;

	onMount(() => {
		// document.addEventListener('wheel', (e) => e.preventDefault(), { passive: false });
		// detect browser is mobile
		if (
			/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
		) {
			$canvasSize = {
				width: 512 * 8,
				height: 512 * 8
			};
		}
		client = createClient({
			authEndpoint: PUBLIC_API_BASE + '/auth'
		});

		updateRooms();
		const acceptedParam = new URLSearchParams(window.location.search).get('acceptedContentWarning') 
		console.log(acceptedParam);
		const accepted = Cookies.get('acceptedContentWarning');
		hideContentModal = false;
		if (accepted || acceptedParam === 'true') {
			hideContentModal = true;
		}
	});

	function contentModal() {
		hideContentModal = true;
		Cookies.set('acceptedContentWarning', 'true', { expires: 10 });
		const params = new URLSearchParams(window.location.search);
		params.set('acceptedContentWarning', 'true');
		window.history.replaceState(null, '', `?${params.toString()}`);
		window.parent.postMessage({ queryString: params.toString() }, '*');
	}

	async function updateRooms() {
		loading = true;
		const roomidParam = new URLSearchParams(window.location.search).get('roomid');
		const res = await fetch(PUBLIC_API_BASE + '/rooms');
		const rooms: RoomResponse[] = await res.json();
		const emptyRoom = rooms.find((room) => room.users_count < MAX_CAPACITY) || null;

		let queriedRoom: string | null = null;
		// init if roomid is set via param
		if (roomidParam) {
			// if room is unlisted, skip the check
			if (roomidParam.startsWith('secret-')) {
				queriedRoom = roomidParam;
			} else {
				// if room is listed, check if it's full
				const room = rooms.find((room) => room.room_id === roomidParam) || null;
				queriedRoom = room && room.users_count < MAX_CAPACITY ? room.room_id : null;
			}
		} else {
			// if roomid is not set via param, select the first empty room
			queriedRoom = emptyRoom ? emptyRoom.room_id : null;
		}
		// if seleceted room is full, select the first empty room
		if (queriedRoom) {
			$selectedRoomID = queriedRoom;
			const params = new URLSearchParams(window.location.search);
			params.set('roomid', queriedRoom);

			window.history.replaceState(null, '', `?${params.toString()}`);
			window.parent.postMessage({ queryString: params.toString() }, '*');
		}
		loading = false;
		return { rooms };
	}
	const initialPresence = {
		cursor: null,
		frame: {
			x: $canvasSize.width / 2 - FRAME_SIZE / 2,
			y: $canvasSize.height / 2 - FRAME_SIZE / 2
		},
		status: Status.dragging,
		currentPrompt: ''
	};
</script>

{#if !hideContentModal}
	<ContentWarningModal on:contentModal={() => contentModal()} />
{/if}
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
