"use client";

import { createContext, useContext, useState, useCallback, useEffect, ReactNode } from "react";
import { api } from "@/lib/api";

interface RestaurantContextType {
  restaurantId: number;
  setRestaurantId: (id: number) => void;
  refreshKey: number;
  triggerRefresh: () => void;
}

const RestaurantContext = createContext<RestaurantContextType>({
  restaurantId: 0,
  setRestaurantId: () => {},
  refreshKey: 0,
  triggerRefresh: () => {},
});

export function RestaurantProvider({ children }: { children: ReactNode }) {
  const [restaurantId, setRestaurantId] = useState(0);
  const [refreshKey, setRefreshKey] = useState(0);
  const triggerRefresh = useCallback(() => setRefreshKey((k) => k + 1), []);

  // Auto-select first available restaurant on load
  useEffect(() => {
    (async () => {
      try {
        const restaurants = await api.getRestaurants();
        if (restaurants.length > 0 && restaurantId === 0) {
          setRestaurantId(restaurants[0].id);
        }
      } catch {
        // no restaurants yet, stay at 0
      }
    })();
  }, []);

  return (
    <RestaurantContext.Provider value={{ restaurantId, setRestaurantId, refreshKey, triggerRefresh }}>
      {children}
    </RestaurantContext.Provider>
  );
}

export function useRestaurant() {
  return useContext(RestaurantContext);
}
