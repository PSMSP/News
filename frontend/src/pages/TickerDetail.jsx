import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  getWatchlist,
  getDirectNews,
  getAdjacentNews,
  markRead,
  submitFeedback,
  addAdjacent,
  removeAdjacent,
} from "../api";

const POLL_INTERVAL = 30000;

export default function TickerDetail() {
  const { watchlistId } = useParams();
  const navigate = useNavigate();

  const [item, setItem] = useState(null);
  const [tab, setTab] = useState("direct");
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);

  // Adjacent form
  const [adjTicker, setAdjTicker] = useState("");
  const [adjCompany, setAdjCompany] = useState("");
  const [adjError, setAdjError] = useState("");

  const loadItem = useCallback(async () => {
    const wl = await getWatchlist();
    const found = wl.find((w) => w.id === watchlistId);
    if (!found) {
      navigate("/");
      return null;
    }
    setItem(found);
    return found;
  }, [watchlistId, navigate]);

  const loadArticles = useCallback(async () => {
    try {
      const fetcher = tab === "direct" ? getDirectNews : getAdjacentNews;
      const data = await fetcher(watchlistId);
      setArticles(data);
    } catch (e) {
      console.error("Failed to load articles:", e);
    } finally {
      setLoading(false);
    }
  }, [watchlistId, tab]);

  useEffect(() => {
    loadItem();
  }, [loadItem]);

  useEffect(() => {
    setLoading(true);
    loadArticles();
    const interval = setInterval(loadArticles, POLL_INTERVAL);
    return () => clearInterval(interval);
  }, [loadArticles]);

  const handleArticleClick = async (article) => {
    if (!article.is_read) {
      try {
        await markRead(article.id);
        setArticles((prev) =>
          prev.map((a) => (a.id === article.id ? { ...a, is_read: true } : a))
        );
      } catch (e) {
        console.error("Failed to mark read:", e);
      }
    }
    window.open(article.url, "_blank", "noopener");
  };

  const handleFeedback = async (articleId, vote) => {
    if (!item) return;
    try {
      await submitFeedback(articleId, item.ticker, vote);
    } catch (e) {
      console.error("Failed to submit feedback:", e);
    }
  };

  const handleAddAdjacent = async (e) => {
    e.preventDefault();
    if (!adjTicker.trim() || !adjCompany.trim()) return;
    setAdjError("");
    try {
      await addAdjacent(watchlistId, {
        adjacent_ticker: adjTicker.trim(),
        adjacent_company: adjCompany.trim(),
      });
      setAdjTicker("");
      setAdjCompany("");
      await loadItem();
    } catch (e) {
      setAdjError(e.message);
    }
  };

  const handleRemoveAdjacent = async (mappingId) => {
    try {
      await removeAdjacent(watchlistId, mappingId);
      await loadItem();
    } catch (e) {
      console.error("Failed to remove adjacent:", e);
    }
  };

  if (!item) {
    return <p className="text-gray-500">Loading...</p>;
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <button
          onClick={() => navigate("/")}
          className="text-gray-400 hover:text-white cursor-pointer"
        >
          &larr; Back
        </button>
        <h2 className="text-xl font-semibold">
          <span className="font-mono">{item.ticker}</span>{" "}
          <span className="text-gray-400 font-normal">{item.company}</span>
        </h2>
      </div>

      {/* Adjacent tickers management */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 mb-6">
        <h3 className="text-sm font-medium text-gray-300 mb-2">Adjacent Tickers</h3>
        {item.adjacent_mappings?.length > 0 ? (
          <div className="flex flex-wrap gap-2 mb-3">
            {item.adjacent_mappings.map((adj) => (
              <span
                key={adj.id}
                className="inline-flex items-center gap-1 bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm"
              >
                <span className="font-mono text-amber-400">{adj.adjacent_ticker}</span>
                <span className="text-gray-500">{adj.adjacent_company}</span>
                <button
                  onClick={() => handleRemoveAdjacent(adj.id)}
                  className="text-gray-600 hover:text-red-400 ml-1 cursor-pointer"
                >
                  &times;
                </button>
              </span>
            ))}
          </div>
        ) : (
          <p className="text-gray-600 text-sm mb-3">No adjacent tickers configured.</p>
        )}
        <form onSubmit={handleAddAdjacent} className="flex gap-2">
          <input
            type="text"
            value={adjTicker}
            onChange={(e) => setAdjTicker(e.target.value.toUpperCase())}
            placeholder="Ticker"
            className="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 w-24"
          />
          <input
            type="text"
            value={adjCompany}
            onChange={(e) => setAdjCompany(e.target.value)}
            placeholder="Company name"
            className="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 flex-1"
          />
          <button
            type="submit"
            disabled={!adjTicker.trim() || !adjCompany.trim()}
            className="bg-gray-700 hover:bg-gray-600 disabled:opacity-40 text-white rounded px-3 py-1 text-sm cursor-pointer disabled:cursor-not-allowed"
          >
            Add
          </button>
        </form>
        {adjError && <p className="text-red-400 text-xs mt-1">{adjError}</p>}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-4 border-b border-gray-800">
        <button
          onClick={() => setTab("direct")}
          className={`px-4 py-2 text-sm font-medium cursor-pointer border-b-2 transition-colors ${
            tab === "direct"
              ? "border-blue-500 text-white"
              : "border-transparent text-gray-500 hover:text-gray-300"
          }`}
        >
          Direct News
        </button>
        <button
          onClick={() => setTab("adjacent")}
          className={`px-4 py-2 text-sm font-medium cursor-pointer border-b-2 transition-colors ${
            tab === "adjacent"
              ? "border-amber-500 text-white"
              : "border-transparent text-gray-500 hover:text-gray-300"
          }`}
        >
          Adjacent News
        </button>
      </div>

      {/* Articles */}
      {loading ? (
        <p className="text-gray-500">Loading articles...</p>
      ) : articles.length === 0 ? (
        <p className="text-gray-500">
          {tab === "direct"
            ? "No direct news articles yet. The scraper will pick up new articles shortly."
            : "No adjacent news. Add adjacent tickers above to see related news here."}
        </p>
      ) : (
        <div className="space-y-1">
          {articles.map((article) => (
            <div
              key={article.id}
              className={`flex items-start gap-3 px-3 py-2 rounded hover:bg-gray-900 transition-colors ${
                article.is_read ? "opacity-60" : ""
              }`}
            >
              <div className="flex-1 min-w-0">
                <button
                  onClick={() => handleArticleClick(article)}
                  className="text-left text-sm text-blue-400 hover:text-blue-300 hover:underline cursor-pointer truncate block w-full"
                >
                  {!article.is_read && (
                    <span className="inline-block w-2 h-2 bg-blue-500 rounded-full mr-2 flex-shrink-0" />
                  )}
                  {article.headline}
                </button>
                <div className="flex items-center gap-2 mt-0.5">
                  {article.source && (
                    <span className="text-xs text-gray-600">{article.source}</span>
                  )}
                  {tab === "adjacent" && (
                    <span className="text-xs text-amber-500">
                      via {article.ticker}
                    </span>
                  )}
                  {article.published_at && (
                    <span className="text-xs text-gray-600">
                      {new Date(article.published_at).toLocaleString()}
                    </span>
                  )}
                </div>
              </div>
              {tab === "adjacent" && (
                <div className="flex gap-1 flex-shrink-0">
                  <button
                    onClick={() => handleFeedback(article.id, 1)}
                    className="text-gray-600 hover:text-green-400 text-sm cursor-pointer"
                    title="Relevant"
                  >
                    &#x1f44d;
                  </button>
                  <button
                    onClick={() => handleFeedback(article.id, -1)}
                    className="text-gray-600 hover:text-red-400 text-sm cursor-pointer"
                    title="Not relevant"
                  >
                    &#x1f44e;
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
