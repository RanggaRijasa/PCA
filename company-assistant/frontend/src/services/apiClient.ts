const localApiDefault = `${window.location.protocol}//${window.location.hostname}:8000`;
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || localApiDefault;

export const useLocalMocks = import.meta.env.VITE_USE_LOCAL_MOCKS === "true";

export class ApiError extends Error {
  code: string;
  status: number;

  constructor(message: string, code = "API_ERROR", status = 500) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
  }
}

export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  const headers = new Headers(init?.headers);
  if (!(init?.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      credentials: "include",
      headers,
    });
  } catch {
    throw new ApiError("The local backend is not reachable. Check that FastAPI is running.", "BACKEND_OFFLINE", 0);
  }

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new ApiError(payload.error || "The request could not be completed.", payload.code || "HTTP_ERROR", response.status);
  }

  return response.json() as Promise<T>;
}
