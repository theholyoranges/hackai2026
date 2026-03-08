"use client";

import { useState } from "react";
import "./globals.css";
import Sidebar from "@/components/layout/Sidebar";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [selectedRestaurant, setSelectedRestaurant] = useState(1);

  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50">
        <Sidebar
          selectedRestaurant={selectedRestaurant}
          onRestaurantChange={setSelectedRestaurant}
        />
        <main className="ml-64 min-h-screen">
          <div className="p-8">{children}</div>
        </main>
      </body>
    </html>
  );
}
