import { sveltekit } from '@sveltejs/kit/vite';
import type { UserConfig } from 'vite';

const config: UserConfig = {
	plugins: [sveltekit()],
	server: {
		// host: "0.0.0.0",
		proxy: {
			'/moon': {
				target: 'https://huggingface.co',
				changeOrigin: true,
				cookieDomainRewrite: 'localhost',
				rewrite: (path) => path.replace(/^\/moon/, '')
			},
			'/uploads': {
				target: 'https://s3.amazonaws.com',
				changeOrigin: true,
				cookieDomainRewrite: 'localhost',
				rewrite: (path) => path.replace(/^\/uploads/, '')
			}
		}
	}
};
export default config;
