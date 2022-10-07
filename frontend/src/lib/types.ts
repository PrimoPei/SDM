export type Presence = {
	cursor: {
		x: number;
		y: number;
	} | null;
	frame: {
		x: number;
		y: number;
	} | null;
	isPrompting: boolean;
	isLoading: boolean;
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
};

export type PromptImgKey = string;
