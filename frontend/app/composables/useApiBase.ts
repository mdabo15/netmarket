/**
 * Resolves the FastAPI base URL. If NUXT_PUBLIC_API_BASE was set explicitly
 * (e.g. a real domain in production), that wins. Otherwise, reuse whatever
 * host was used to reach this page — opening the app from a phone via the
 * PC's LAN IP then automatically talks to the API on that same IP, port
 * 8001, with nothing to reconfigure when the network (or the PC's IP on it)
 * changes. useRequestURL() covers both sides on its own: during SSR it
 * reads the incoming request's Host header (so the phone's own IP ends up
 * in the server-rendered HTML, not "localhost" — which the phone would
 * otherwise briefly try to load images from before hydration corrected it);
 * on the client it's window.location. See nuxt.config.ts's
 * `devServer.host: '0.0.0.0'` for the other half of this (the page itself
 * must also be reachable from the LAN).
 */
export function useApiBase(): string {
  const config = useRuntimeConfig()
  if (config.public.apiBase) return config.public.apiBase
  const { protocol, hostname } = useRequestURL()
  return `${protocol}//${hostname}:8001`
}
