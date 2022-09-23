import { sveltekit } from '@sveltejs/kit/vite';
import type { UserConfig } from 'vite';

const config: UserConfig = {
	plugins: [sveltekit()],
	server: {
		proxy: {
			'/moon': {
				target: 'https://huggingface.co',
				changeOrigin: true,
				cookieDomainRewrite: 'localhost',
				rewrite: (path) => path.replace(/^\/moon/, '')
			}
		}
	}
};

export default config;
