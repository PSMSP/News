import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { getWatchlist, getUnreadCounts, addToWatchlist, removeFromWatchlist } from "../api";

const POLL_INTERVAL = 30000; // 30 seconds

export default function Dashboard() {
  const navigate = useNavigate();
  const [watchlist, setWatchlist] = useState([]);
  const [counts, setCounts] = useState({});
  const [ticker, setTicker] = useState("");
  const [company, setCompany] = useState("");
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState("");

  const loadData = useCallback(async () => {
    try {
      const [wl, ct] = await Promise.all([getWatchlist(), getUnreadCounts()]);
      setWatchlist(wl);
      const countMap = {};
      for (const c of ct) {
        countMap[c.ticker] = c;
      }
      setCounts(countMap);
    } catch (e) {
      console.error("Failed to load data:", e);
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, POLL_INTERVAL);
    return () => clearInterval(interval);
  }, [loadData]);

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!ticker.trim() || !company.trim()) return;
    setAdding(true);
    setError("");
    try {
      await addToWatchlist({ ticker: ticker.trim(), company: company.trim() });
      setTicker("");
      setCompany("");
      await loadData();
    } catch (e) {
      setError(e.message);
    } finally {
      setAdding(false);
    }
  };

  const handleRemove = async (id, e) => {
    e.stopPropagation();
    try {
      await removeFromWatchlist(id);
      await loadData();
    } catch (e) {
      console.error("Failed to remove:", e);
    }
  };

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Watchlist</h2>

      {/* Add ticker form */}
      <form onSubmit={handleAdd} className="flex gap-2 mb-6">
        <input
          type="text"
          value={ticker}
          onChange={(e) => setTicker(e.target.value.toUpperCase())}
          placeholder="Ticker (e.g. AAPL)"
          className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 w-32"
        />
        <input
          type="text"
          value={company}
          onChange={(e) => setCompany(e.target.value)}
          placeholder="Company name"
          className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 flex-1"
        />
        <button
          type="submit"
          disabled={adding || !ticker.trim() || !company.trim()}
          className="bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white rounded px-4 py-2 font-medium cursor-pointer disabled:cursor-not-allowed"
        >
          Add
        </button>
      </form>

      {error && (
        <p className="text-red-400 text-sm mb-4">{error}</p>
      )}

      {/* Watchlist items */}
      {watchlist.length === 0 ? (
        <p className="text-gray-500">
          No tickers on your watchlist. Add one above to get started.
        </p>
      ) : (
        <div className="space-y-2">
          {watchlist.map((item) => {
            const c = counts[item.ticker] || {};
            return (
              <div
                key={item.id}
                onClick={() => navigate(`/ticker/${item.id}`)}
                className="flex items-center justify-between bg-gray-900 border border-gray-800 rounded-lg px-4 py-3 hover:border-gray-600 cursor-pointer transition-colors"
              >
                <div className="flex items-center gap-4">
                  <span className="font-mono font-semibold text-white">
                    {item.ticker}
                  </span>
                  <span className="text-gray-400 text-sm">{item.company}</span>
                </div>
                <div className="flex items-center gap-4">
                  {(c.direct_unread > 0) && (
                    <span className="bg-blue-600 text-white text-xs font-medium px-2 py-0.5 rounded-full">
                      {c.direct_unread} direct
                    </span>
                  )}
                  {(c.adjacent_unread > 0) && (
                    <span className="bg-amber-600 text-white text-xs font-medium px-2 py-0.5 rounded-full">
                      {c.adjacent_unread} adjacent
                    </span>
                  )}
                  <span className="text-gray-600 text-xs">
                    {item.adjacent_mappings?.length || 0} adjacents
                  </span>
                  <button
                    onClick={(e) => handleRemove(item.id, e)}
                    className="text-gray-600 hover:text-red-400 text-sm cursor-pointer"
                    title="Remove from watchlist"
                  >
                    Remove
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
