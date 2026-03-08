"use client";

import { useState, useRef, useEffect } from "react";

import { api } from "@/lib/api";
import { useRestaurant } from "@/context/RestaurantContext";

interface Message {
  role: "user" | "assistant";
  content: string;
}

const SUGGESTED_QUESTIONS = [
  "What should I promote this week?",
  "Why is waste increasing?",
  "What strategies worked best?",
  "Which menu items should I reprice?",
  "What are my top-selling items?",
  "When should I post on social media?",
];

export default function ChatPage() {
  
  const { restaurantId } = useRestaurant();

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async (text: string) => {
    if (!text.trim() || loading) return;

    const userMessage: Message = { role: "user", content: text.trim() };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const data = await api.chat(restaurantId, text.trim());
      const assistantMessage: Message = {
        role: "assistant",
        content:
          typeof data === "string"
            ? data
            : data?.response ?? data?.message ?? JSON.stringify(data),
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      const errorMessage: Message = {
        role: "assistant",
        content: `Sorry, something went wrong: ${err.message ?? "Unknown error"}. Please try again.`,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 flex flex-col h-[calc(100vh-4rem)]">
      <h1 className="text-3xl font-bold text-gray-900 mb-6 shrink-0">
        Chat with Bri
      </h1>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto space-y-4 pb-4 min-h-0">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="bg-indigo-50 rounded-full p-4 mb-4">
              <svg
                className="w-10 h-10 text-indigo-600"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                />
              </svg>
            </div>
            <p className="text-gray-600 text-lg font-medium mb-2">
              Ask me anything about your restaurant
            </p>
            <p className="text-gray-400 text-sm mb-6 max-w-md">
              I can help with menu optimization, inventory management, marketing
              strategies, and more.
            </p>

            {/* Suggested Questions */}
            <div className="flex flex-wrap justify-center gap-2 max-w-lg">
              {SUGGESTED_QUESTIONS.map((q, i) => (
                <button
                  key={i}
                  onClick={() => sendMessage(q)}
                  className="bg-white border border-gray-200 hover:border-indigo-300 hover:bg-indigo-50 text-gray-700 text-sm px-4 py-2 rounded-full transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${
              msg.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <div
              className={`max-w-[75%] rounded-2xl px-4 py-3 ${
                msg.role === "user"
                  ? "bg-indigo-600 text-white"
                  : "bg-gray-100 text-gray-800"
              }`}
            >
              <p className="text-sm whitespace-pre-wrap leading-relaxed">
                {msg.content}
              </p>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-2xl px-4 py-3">
              <div className="flex items-center gap-1.5">
                <div
                  className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                  style={{ animationDelay: "0ms" }}
                />
                <div
                  className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                  style={{ animationDelay: "150ms" }}
                />
                <div
                  className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                  style={{ animationDelay: "300ms" }}
                />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Questions (when conversation is active) */}
      {messages.length > 0 && !loading && (
        <div className="flex flex-wrap gap-2 py-2 shrink-0">
          {SUGGESTED_QUESTIONS.slice(0, 3).map((q, i) => (
            <button
              key={i}
              onClick={() => sendMessage(q)}
              disabled={loading}
              className="bg-white border border-gray-200 hover:border-indigo-300 hover:bg-indigo-50 disabled:opacity-50 text-gray-600 text-xs px-3 py-1.5 rounded-full transition-colors"
            >
              {q}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <form onSubmit={handleSubmit} className="shrink-0 pt-2">
        <div className="flex items-center gap-3">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about your restaurant..."
            disabled={loading}
            className="flex-1 border border-gray-300 rounded-xl px-4 py-3 text-gray-800 placeholder-gray-400 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none disabled:bg-gray-50 transition-colors"
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-medium px-5 py-3 rounded-xl transition-colors shrink-0"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
              />
            </svg>
          </button>
        </div>
      </form>
    </div>
  );
}
