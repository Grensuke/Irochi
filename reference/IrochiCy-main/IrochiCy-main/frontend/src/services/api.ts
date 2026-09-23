/* ═══════════════════════════════════════════════════════════════
   SIH-26145 API Client
   Typed fetch wrapper with auth, retry, and mock mode support
   ═══════════════════════════════════════════════════════════════ */

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';
const IS_MOCK = import.meta.env.VITE_MOCK !== 'false';

function delay(ms: number): Promise<void> {
  return new Promise(r => setTimeout(r, ms));
}

class ApiClient {
  private token: string | null = null;

  setToken(token: string | null) { this.token = token; }

  private headers(): HeadersInit {
    const h: HeadersInit = { 'Content-Type': 'application/json' };
    if (this.token) h['Authorization'] = `Bearer ${this.token}`;
    return h;
  }

  async request<T>(method: string, path: string, body?: unknown, retries = 3): Promise<T> {
    if (IS_MOCK) {
      await delay(100 + Math.random() * 200);
      throw new Error('Mock mode — use mock service directly');
    }

    let lastError: Error | null = null;
    for (let attempt = 0; attempt < retries; attempt++) {
      try {
        const res = await fetch(`${API_BASE}${path}`, {
          method,
          headers: this.headers(),
          body: body ? JSON.stringify(body) : undefined,
        });

        if (res.status === 401) {
          this.token = null;
          window.location.href = '/login';
          throw new Error('Unauthorized');
        }
        if (res.status === 403) throw new Error('Access denied');
        if (res.status === 404) throw new Error('Not found');
        if (res.status === 429) {
          const backoff = Math.pow(2, attempt) * 1000;
          await delay(backoff);
          continue;
        }
        if (res.status >= 500) {
          lastError = new Error(`Server error: ${res.status}`);
          if (attempt < retries - 1) {
            await delay(Math.pow(2, attempt) * 500);
            continue;
          }
          throw lastError;
        }

        return await res.json() as T;
      } catch (err) {
        lastError = err instanceof Error ? err : new Error(String(err));
        if (attempt >= retries - 1) throw lastError;
      }
    }
    throw lastError || new Error('Request failed');
  }

  get<T>(path: string) { return this.request<T>('GET', path); }
  post<T>(path: string, body?: unknown) { return this.request<T>('POST', path, body); }
  put<T>(path: string, body?: unknown) { return this.request<T>('PUT', path, body); }
  del<T>(path: string) { return this.request<T>('DELETE', path); }
}

export const api = new ApiClient();
export default api;
