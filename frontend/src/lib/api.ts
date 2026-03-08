const API_BASE = "/api/v1";

export async function fetchAPI(path: string, options?: RequestInit) {
  const url = `${API_BASE}${path}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`API error ${response.status}: ${errorBody}`);
  }

  return response.json();
}

export const api = {
  // Restaurants
  getRestaurants: () => fetchAPI("/restaurants"),

  // Dashboard
  getDashboard: (id: number) => fetchAPI(`/analytics/dashboard/${id}`),

  // Analytics
  getMenuAnalytics: (id: number) => fetchAPI(`/analytics/menu/${id}`),
  getInventoryAnalytics: (id: number) => fetchAPI(`/analytics/inventory/${id}`),
  getSocialAnalytics: (id: number) => fetchAPI(`/analytics/social/${id}`),

  // Recommendations
  getRecommendations: (id: number) => fetchAPI(`/recommendations/${id}`),
  generateRecommendations: (id: number) =>
    fetchAPI(`/recommendations/generate/${id}`, { method: "POST" }),
  updateRecommendationStatus: (id: number, status: string) =>
    fetchAPI(`/recommendations/${id}/status`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    }),

  // Strategy History
  getStrategyHistory: (id: number) => fetchAPI(`/strategies/history/${id}`),
  updateStrategyStatus: (id: number, status: string) =>
    fetchAPI(`/strategies/history/${id}/status`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    }),

  // Uploads
  uploadCSV: (type: string, restaurantId: number, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return fetchAPI(`/uploads/${type}?restaurant_id=${restaurantId}`, {
      method: "POST",
      body: form,
    });
  },

  // Chat
  chat: (restaurantId: number, message: string) =>
    fetchAPI("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ restaurant_id: restaurantId, message }),
    }),

  // Seed demo data
  seedDemo: () => fetchAPI("/uploads/seed-demo", { method: "POST" }),
};
