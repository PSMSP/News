const getUsername = () => localStorage.getItem("username") || "";

const headers = () => ({
  "Content-Type": "application/json",
  "X-Username": getUsername(),
});

async function request(url, options = {}) {
  const res = await fetch(url, {
    ...options,
    headers: { ...headers(), ...options.headers },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  if (res.status === 204) return null;
  return res.json();
}

// Users
export const getMe = () => request("/api/users/me");

// Watchlist
export const getWatchlist = () => request("/api/watchlist/");
export const addToWatchlist = (data) =>
  request("/api/watchlist/", { method: "POST", body: JSON.stringify(data) });
export const removeFromWatchlist = (id) =>
  request(`/api/watchlist/${id}`, { method: "DELETE" });

// Adjacents
export const addAdjacent = (watchlistId, data) =>
  request(`/api/watchlist/${watchlistId}/adjacents`, {
    method: "POST",
    body: JSON.stringify(data),
  });
export const removeAdjacent = (watchlistId, mappingId) =>
  request(`/api/watchlist/${watchlistId}/adjacents/${mappingId}`, {
    method: "DELETE",
  });

// News
export const getUnreadCounts = () => request("/api/news/counts");
export const getDirectNews = (watchlistId, limit = 50, offset = 0) =>
  request(`/api/news/${watchlistId}/direct?limit=${limit}&offset=${offset}`);
export const getAdjacentNews = (watchlistId, limit = 50, offset = 0) =>
  request(`/api/news/${watchlistId}/adjacent?limit=${limit}&offset=${offset}`);
export const markRead = (articleId) =>
  request(`/api/news/${articleId}/read`, { method: "POST" });
export const submitFeedback = (articleId, ticker, vote) =>
  request(`/api/news/${articleId}/feedback/${ticker}`, {
    method: "POST",
    body: JSON.stringify({ vote }),
  });
