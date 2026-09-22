const BASE_PATH = "/api/backend";

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

export interface ApiFetchInit extends RequestInit {
  /** Send the browser to /login on a 401 (an expired session). Off for the login call itself. */
  redirectOnUnauthorized?: boolean;
}

async function readErrorMessage(response: Response): Promise<string> {
  try {
    const body = await response.json();
    return body?.error?.message ?? response.statusText;
  } catch {
    return response.statusText;
  }
}

export async function apiFetch<T>(
  path: string,
  { redirectOnUnauthorized = true, ...init }: ApiFetchInit = {},
): Promise<T> {
  // A FormData body needs the browser to set its own multipart boundary; don't force JSON on it.
  const isFormData = init.body instanceof FormData;
  const response = await fetch(`${BASE_PATH}${path}`, {
    ...init,
    headers: isFormData ? init.headers : { "Content-Type": "application/json", ...init.headers },
  });
  if (!response.ok) {
    if (response.status === 401 && redirectOnUnauthorized) {
      // A full page load on purpose: it drops client state once the session has ended.
      // eslint-disable-next-line @next/next/no-location-assign-relative-destination
      window.location.assign("/login");
    }
    throw new ApiError(response.status, await readErrorMessage(response));
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}
