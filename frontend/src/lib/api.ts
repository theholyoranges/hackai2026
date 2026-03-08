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
  getRestaurant: (id: number) => fetchAPI(`/restaurants/${id}`),
  createRestaurant: (data: { name: string; cuisine_type?: string; location?: string }) =>
    fetchAPI("/restaurants", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }),

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
  elaborateRecommendation: (data: {
    title: string;
    description: string;
    target_item?: string;
    context?: Record<string, any>;
  }) =>
    fetchAPI("/recommendations/elaborate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }),

  // Strategy History
  getStrategyHistory: (id: number) => fetchAPI(`/strategies/history/${id}`),
  getStrategyProgress: (id: number) => fetchAPI(`/strategies/history/${id}/progress`),
  evaluateStrategy: (historyId: number) =>
    fetchAPI(`/strategies/history/${historyId}/evaluate`, { method: "POST" }),
  adoptStrategy: (data: {
    restaurant_id: number;
    strategy_code: string;
    menu_item_name?: string;
    title: string;
    expected_impact?: string;
    evidence?: Record<string, any>;
  }) =>
    fetchAPI("/strategies/adopt", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }),
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

  // POS Sales upload (auto-converts standard POS format)
  uploadPOSSales: (restaurantId: number, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return fetchAPI(`/uploads/pos-sales?restaurant_id=${restaurantId}`, {
      method: "POST",
      body: form,
    });
  },

  // AI Recipe Generation
  generateRecipes: (restaurantId: number) =>
    fetchAPI(`/uploads/generate-recipes?restaurant_id=${restaurantId}`, {
      method: "POST",
    }),

  // Seed demo data
  seedDemo: () => fetchAPI("/uploads/seed-demo", { method: "POST" }),
};
