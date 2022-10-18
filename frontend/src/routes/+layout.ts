import { PUBLIC_API_BASE } from '$env/static/public';

export async function load({ fetch }) {
    const rooms = await fetch(PUBLIC_API_BASE + "/rooms").then((res) => res.json());
    return { rooms };
}