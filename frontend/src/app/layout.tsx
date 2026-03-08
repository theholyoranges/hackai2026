"use client";

import "./globals.css";
import { usePathname } from "next/navigation";
import Sidebar from "@/components/layout/Sidebar";
import { RestaurantProvider, useRestaurant } from "@/context/RestaurantContext";

function LayoutInner({ children }: { children: React.ReactNode }) {
  const { restaurantId, setRestaurantId, refreshKey } = useRestaurant();
  const pathname = usePathname();
  const isLogin = pathname === "/login";

  if (isLogin) {
    return <>{children}</>;
  }

  return (
    <>
      <Sidebar
        selectedRestaurant={restaurantId}
        onRestaurantChange={setRestaurantId}
        refreshKey={refreshKey}
      />
      <main className="ml-64 min-h-screen">
        <div className="p-8">{children}</div>
      </main>
    </>
  );
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50">
        <RestaurantProvider>
          <LayoutInner>{children}</LayoutInner>
        </RestaurantProvider>
      </body>
    </html>
  );
}
