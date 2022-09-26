<script lang="ts">
	import Cursor from '$lib/Cursor.svelte';
	import Frame from '$lib/Frame.svelte';
	import Canvas from '$lib/Canvas.svelte';
	import Menu from '$lib/Menu.svelte';
	import type { Room } from '@liveblocks/client';
	import { onDestroy } from 'svelte';
	import { currZoomTransform } from '$lib/store';

	/**
	 * The main Liveblocks code for the example.
	 * Check in src/routes/index.svelte to see the setup code.
	 */

	export let room: Room;

	// Get initial values for presence and others
	let myPresence = room.getPresence();
	let others = room.getOthers();

	// Subscribe to further changes
	const unsubscribeMyPresence = room.subscribe('my-presence', (presence) => {
		myPresence = presence;
	});

	const unsubscribeOthers = room.subscribe('others', (otherUsers) => {
		others = otherUsers;
	});

	// Unsubscribe when unmounting
	onDestroy(() => {
		unsubscribeMyPresence();
		unsubscribeOthers();
	});

	// Update cursor presence to current pointer location
	function handlePointerMove(event: PointerEvent) {
		event.preventDefault();
		room.updatePresence({
			cursor: {
				x: Math.round(event.layerX),
				y: Math.round(event.layerY)
			}
		});
	}

	// When the pointer leaves the page, set cursor presence to null
	function handlePointerLeave() {
		room.updatePresence({
			cursor: null
		});
	}

	const COLORS = [
		'#E57373',
		'#9575CD',
		'#4FC3F7',
		'#81C784',
		'#FFF176',
		'#FF8A65',
		'#F06292',
		'#7986CB'
	];
</script>

<div class="relative">
	<div class="z-0">
		<h3 class="text-xl">TESTS</h3>
	</div>
	<main class="z-10 relative">
		<!-- Show the current user's cursor location -->
		<div class="text">
			{myPresence?.cursor
				? `${myPresence.cursor.x} × ${myPresence.cursor.y}`
				: 'Move your cursor to broadcast its position to other people in the room.'}
		</div>
		{#if myPresence?.cursor}
			<Frame x={myPresence.cursor.x} y={myPresence.cursor.y} transform={$currZoomTransform} />
		{/if}

		<!-- When others connected, iterate through others and show their cursors -->
		{#if others}
			{#each [...others] as { connectionId, presence } (connectionId)}
				{#if presence?.cursor}
					<Cursor
						color={COLORS[connectionId % COLORS.length]}
						x={presence.cursor.x}
						y={presence.cursor.y}
					/>
					<Frame x={presence.cursor.x} y={presence.cursor.y} transform={$currZoomTransform} />
				{/if}
			{/each}
		{/if}
		<Canvas />
	</main>
</div>
<div class="fixed bottom-0 left-0 right-0 z-50 my-2">
	<Menu />
</div>

<style lang="postcss" scoped>
	main {
		/* @apply fixed top-0 left-0 w-screen h-screen flex flex-col items-center justify-center touch-none bg-white; */
		/* position: absolute;
		top: 0;
		left: 0;
		width: 100vw;
		height: 100vh;
		display: flex;
		place-content: center;
		place-items: center;
		touch-action: none;
        background-color: white; */
	}

	.text {
		max-width: 380px;
		margin: 0 16px;
		text-align: center;
	}
</style>
