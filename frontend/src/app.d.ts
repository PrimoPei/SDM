// See https://kit.svelte.dev/docs/types#app
// for information about these interfaces
// and what to do when importing types
import type { ZoomTransform } from 'd3-zoom';

declare global {
	namespace App {
		// interface Locals {}
		// interface PageData {}
		// interface Error {}
		// interface Platform {}
		interface Window {
			parentIFrame: unknown;
		}
	}
	interface Event {
		transform: ZoomTransform;
		x: number;
		y: number;
		subject: {
			x: number;
			y: number;
		}
		sourceEvent: PointerEvent | MouseEvent | TouchEvent
	}
}
