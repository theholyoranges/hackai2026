"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";
import {
  LayoutDashboard,
  UtensilsCrossed,
  Package,
  Share2,
  Lightbulb,
  History,
  Upload,
  MessageSquare,
  ChevronDown,
  ChefHat,
} from "lucide-react";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/menu-insights", label: "Menu Insights", icon: UtensilsCrossed },
  { href: "/inventory-insights", label: "Inventory", icon: Package },
  { href: "/social-insights", label: "Social", icon: Share2 },
  { href: "/recommendations", label: "Recommendations", icon: Lightbulb },
  { href: "/strategy-history", label: "Strategy History", icon: History },
  { href: "/upload", label: "Upload", icon: Upload },
  { href: "/chat", label: "Chat", icon: MessageSquare },
];

const demoRestaurants = [
  { id: 1, name: "The Golden Fork" },
  { id: 2, name: "Sakura Sushi Bar" },
];

interface SidebarProps {
  selectedRestaurant: number;
  onRestaurantChange: (id: number) => void;
}

export default function Sidebar({
  selectedRestaurant,
  onRestaurantChange,
}: SidebarProps) {
  const pathname = usePathname();
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const currentRestaurant = demoRestaurants.find(
    (r) => r.id === selectedRestaurant
  );

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-slate-900 text-white flex flex-col z-50">
      {/* App Title */}
      <div className="p-6 border-b border-slate-700">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
            <ChefHat className="w-6 h-6" />
          </div>
          <div>
            <h1 className="font-bold text-lg leading-tight">Restaurant</h1>
            <p className="text-xs text-slate-400">Growth Copilot</p>
          </div>
        </div>
      </div>

      {/* Restaurant Selector */}
      <div className="px-4 py-4 border-b border-slate-700">
        <label className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-2 block">
          Restaurant
        </label>
        <div className="relative">
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="w-full flex items-center justify-between bg-slate-800 hover:bg-slate-750 rounded-lg px-3 py-2.5 text-sm transition-colors"
          >
            <span className="truncate">
              {currentRestaurant?.name ?? "Select..."}
            </span>
            <ChevronDown
              className={clsx(
                "w-4 h-4 text-slate-400 transition-transform",
                dropdownOpen && "rotate-180"
              )}
            />
          </button>
          {dropdownOpen && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-slate-800 rounded-lg border border-slate-700 overflow-hidden shadow-lg">
              {demoRestaurants.map((r) => (
                <button
                  key={r.id}
                  onClick={() => {
                    onRestaurantChange(r.id);
                    setDropdownOpen(false);
                  }}
                  className={clsx(
                    "w-full text-left px-3 py-2.5 text-sm hover:bg-slate-700 transition-colors",
                    r.id === selectedRestaurant && "bg-slate-700 text-blue-400"
                  )}
                >
                  {r.name}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4 px-3">
        <ul className="space-y-1">
          {navItems.map((item) => {
            const isActive =
              pathname === item.href ||
              (item.href !== "/" && pathname.startsWith(item.href));
            const Icon = item.icon;

            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={clsx(
                    "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                    isActive
                      ? "bg-blue-600 text-white"
                      : "text-slate-300 hover:bg-slate-800 hover:text-white"
                  )}
                >
                  <Icon className="w-5 h-5 flex-shrink-0" />
                  <span>{item.label}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-slate-700">
        <p className="text-xs text-slate-500 text-center">
          Powered by AI Analytics
        </p>
      </div>
    </aside>
  );
}
