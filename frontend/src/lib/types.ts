export enum Status {
	ready = 'ready',
	loading = 'loading',
	prompting = 'prompting',
	processing = 'processing',
	dragging = 'dragging',
	masking = 'masking',
}

export type Presence = {
	cursor: {
		x: number;
		y: number;
	} | null;
	frame: {
		x: number;
		y: number;
	} | null;
	status: Status;
	currentPrompt: string
}

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
	room: string;
};

export type PromptImgKey = string;

export interface RoomResponse {
	id: number;
	room_id: string;
	users_count: number;
}


export enum ConnectionStatus {
	"closed" = "closed",
	"authenticating" = "authenticating",
	"unavailable" = "unavailable",
	"failed" = "failed",
	"open" = "open",
	"connecting" = "connecting",
}
export type TConnectionStatus = keyof typeof ConnectionStatus
