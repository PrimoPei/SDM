import type { JsonObject } from "@liveblocks/client";


export interface Presence extends JsonObject {
	cursor: {
		x: number;
		y: number;
	} | null;
};

export type Storage = {
	// animals: LiveList<string>,
	// ...
};

export type User = string;

export type PromptImgObject = {
	prompt: string;
	imgURL: string;
	position: {
		x: number;
		y: number;
	}
	date: number;
	id: string;
};

export type PromptImgKey = string;
