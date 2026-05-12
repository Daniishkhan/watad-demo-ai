const BACKEND_BASE_URL = process.env.WATAD_API_BASE_URL ?? "http://127.0.0.1:8000";

type RouteContext = {
  params: Promise<{ path: string[] }>;
};

async function proxyWatadRequest(request: Request, context: RouteContext): Promise<Response> {
  const { path } = await context.params;
  const incomingUrl = new URL(request.url);
  const targetUrl = new URL(path.join("/"), withTrailingSlash(BACKEND_BASE_URL));
  targetUrl.search = incomingUrl.search;

  const headers = new Headers(request.headers);
  headers.delete("host");
  headers.delete("content-length");

  const body = request.method === "GET" || request.method === "HEAD"
    ? undefined
    : await request.arrayBuffer();

  const response = await fetch(targetUrl, {
    method: request.method,
    headers,
    body,
    cache: "no-store",
  });

  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: response.headers,
  });
}

function withTrailingSlash(value: string): string {
  return value.endsWith("/") ? value : `${value}/`;
}

export const GET = proxyWatadRequest;
export const POST = proxyWatadRequest;
export const OPTIONS = proxyWatadRequest;
