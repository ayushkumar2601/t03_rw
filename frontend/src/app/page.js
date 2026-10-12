"use client";

import { useEffect, useRef, useState } from "react";

const SUGGESTIONS = [
  {
    tag: "Founder",
    title: "Who is the founder of Agarwal Constructions?",
    desc: "Leadership & early beginnings",
  },
  {
    tag: "Head Office",
    title: "What is the head office address and phone number?",
    desc: "Official Kolkata HQ contact details",
  },
  {
    tag: "Founding Year",
    title: "In what year was the company established and with what capital?",
    desc: "1995 genesis & investment",
  },
  {
    tag: "Contact Email",
    title: "Can I contact the company by email? What is the email address?",
    desc: "Official inquiries & correspondence",
  },
  {
    tag: "Vision",
    title: "What is the company's vision for future expansion?",
    desc: "Tripura & pan-India scale",
  },
  {
    tag: "Safety Check",
    title: "What is the return and refund policy for commercial leases?",
    desc: "Tests verifiable abstention guardrail",
  },
];

function renderFormattedContent(content) {
  if (!content) return null;

  // Clean any vertical single-word line breaks if present
  const lines = content
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean);
  let cleaned = content;
  if (lines.length > 4) {
    const avgWords =
      lines.reduce((acc, l) => acc + l.split(/\s+/).length, 0) / lines.length;
    if (avgWords < 2.5) {
      cleaned = lines.join(" ");
    }
  }

  // Split into paragraphs by double newlines
  const paragraphs = cleaned.split(/\n\s*\n/).filter((p) => p.trim());
  if (paragraphs.length <= 1) {
    return <p className="bubble-paragraph">{cleaned}</p>;
  }

  return paragraphs.map((para, pIdx) => (
    <p key={pIdx} className="bubble-paragraph">
      {para}
    </p>
  ));
}

export default function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [backendStatus, setBackendStatus] = useState({
    ready: false,
    checking: true,
    provider: "ollama",
    model: "llama3",
    chunks: 194,
    error: null,
  });
  const [expandedSources, setExpandedSources] = useState({});
  const [copiedId, setCopiedId] = useState(null);

  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  // Check backend readiness on initial mount
  useEffect(() => {
    async function checkReadiness() {
      try {
        // Try through Next.js proxy first, fallback to direct
        let res;
        try {
          res = await fetch("/api/backend/ready");
        } catch {
          res = await fetch("http://127.0.0.1:8000/ready");
        }

        if (res.ok) {
          const data = await res.json();
          setBackendStatus({
            ready: data.status === "ready",
            checking: false,
            provider: data.llm_provider || "ollama",
            model: data.llm_model || "llama3",
            chunks: data.indexed_chunks || 194,
            error: null,
          });
        } else {
          setBackendStatus((prev) => ({
            ...prev,
            ready: false,
            checking: false,
            error: "Backend responded with non-200 status",
          }));
        }
      } catch (err) {
        setBackendStatus((prev) => ({
          ...prev,
          ready: false,
          checking: false,
          error: err.message || "Failed to reach backend",
        }));
      }
    }

    checkReadiness();
    const interval = setInterval(checkReadiness, 15000);
    return () => clearInterval(interval);
  }, []);

  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  // Adjust textarea height dynamically
  const handleInputChange = (e) => {
    setInput(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        140
      )}px`;
    }
  };

  const toggleSources = (msgId) => {
    setExpandedSources((prev) => ({
      ...prev,
      [msgId]: !prev[msgId],
    }));
  };

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleSend = async (questionToSend) => {
    const question = (questionToSend || input).trim();
    if (!question || isLoading) return;

    const userMessageId = `user_${Date.now()}`;
    const userMessage = {
      id: userMessageId,
      role: "user",
      content: question,
      timestamp: new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
    setIsLoading(true);

    const assistantMessageId = `ai_${Date.now()}`;

    try {
      let res;
      try {
        res = await fetch("/api/backend/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question }),
        });
      } catch {
        res = await fetch("http://127.0.0.1:8000/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question }),
        });
      }

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(
          errorData.detail || `Server error (${res.status}): Please check backend service.`
        );
      }

      const data = await res.json();

      const aiMessage = {
        id: assistantMessageId,
        role: "assistant",
        content: data.answer,
        status: data.status,
        sources: data.sources || [],
        retrieval: data.retrieval || { chunks_retrieved: 0, chunks_used: 0 },
        timestamp: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
      };

      setMessages((prev) => [...prev, aiMessage]);

      // Automatically expand sources if citations exist
      if (data.sources && data.sources.length > 0) {
        setExpandedSources((prev) => ({ ...prev, [assistantMessageId]: true }));
      }
    } catch (err) {
      const errorMessage = {
        id: assistantMessageId,
        role: "assistant",
        content: `Error: ${err.message}. Ensure the FastAPI server is running with 'uvicorn main:app --reload'.`,
        status: "error",
        sources: [],
        retrieval: { chunks_retrieved: 0, chunks_used: 0 },
        timestamp: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const clearChat = () => {
    if (messages.length === 0) return;
    if (window.confirm("Are you sure you want to clear the conversation?")) {
      setMessages([]);
      setExpandedSources({});
    }
  };

  return (
    <div className="app-layout">
      {/* Header */}
      <header className="app-header">
        <div className="brand-section">
          <div className="brand-icon-wrapper" aria-hidden="true">
            <svg
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
              />
            </svg>
          </div>
          <div className="brand-info">
            <h1>Agarwal Constructions RAG AI</h1>
            <p>Verified Knowledge Base Assistant • Zero Hallucination</p>
          </div>
        </div>

        <div className="header-status-area">
          <div
            className="status-indicator"
            title={
              backendStatus.error ||
              `Provider: ${backendStatus.provider} | Model: ${backendStatus.model}`
            }
          >
            <span
              className={`pulse-dot ${
                backendStatus.ready ? "" : "error"
              }`}
            />
            <span>
              {backendStatus.checking
                ? "Checking Backend..."
                : backendStatus.ready
                ? `${backendStatus.provider.toUpperCase()} (${backendStatus.model}) • ${
                    backendStatus.chunks
                  } Chunks`
                : "Backend Offline"}
            </span>
          </div>

          {messages.length > 0 && (
            <button
              onClick={clearChat}
              className="btn-header-action"
              title="Clear conversation"
            >
              <svg
                width="14"
                height="14"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
              <span>Clear</span>
            </button>
          )}
        </div>
      </header>

      {/* Main Chat Viewport */}
      <main className="chat-viewport">
        {messages.length === 0 ? (
          <section className="welcome-hero">
            <div className="welcome-badge">
              <span>✦</span> Verified Knowledge Base RAG
            </div>
            <h2>What would you like to know about the company?</h2>
            <p>
              Ask questions directly against the company knowledge base PDF.
              Every answer is verified against retrieved chunks with exact page
              citations.
            </p>

            <div className="suggestions-grid">
              {SUGGESTIONS.map((item, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSend(item.title)}
                  className="suggestion-card"
                >
                  <div className="suggestion-card-header">
                    <span>•</span>
                    <span>{item.tag}</span>
                  </div>
                  <div className="suggestion-card-query">{item.title}</div>
                </button>
              ))}
            </div>
          </section>
        ) : (
          messages.map((msg) => (
            <div key={msg.id} className={`message-row ${msg.role}`}>
              <div className={`avatar-badge ${msg.role}`}>
                {msg.role === "assistant" ? "AI" : "You"}
              </div>

              <div className="message-bubble-wrapper">
                <div className="message-bubble">
                  {renderFormattedContent(msg.content)}

                  {msg.role === "assistant" && (
                    <div className="response-meta-bar">
                      {msg.status === "answered" && (
                        <span className="meta-status-pill answered">
                          <svg
                            width="12"
                            height="12"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth="2.5"
                              d="M5 13l4 4L19 7"
                            />
                          </svg>
                          Grounded with Citations
                        </span>
                      )}

                      {msg.status === "insufficient_evidence" && (
                        <span className="meta-status-pill abstain">
                          <svg
                            width="12"
                            height="12"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth="2.5"
                              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                            />
                          </svg>
                          Abstained (No Evidence)
                        </span>
                      )}

                      {msg.retrieval && (
                        <span className="meta-retrieval-pill">
                          Retrieved: {msg.retrieval.chunks_retrieved} chunks •{" "}
                          Used: {msg.retrieval.chunks_used}
                        </span>
                      )}

                      <button
                        onClick={() => copyToClipboard(msg.content, msg.id)}
                        className="btn-copy-answer"
                        title="Copy answer"
                      >
                        {copiedId === msg.id ? (
                          <>
                            <svg
                              width="12"
                              height="12"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth="2"
                                d="M5 13l4 4L19 7"
                              />
                            </svg>
                            <span>Copied</span>
                          </>
                        ) : (
                          <>
                            <svg
                              width="12"
                              height="12"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth="2"
                                d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                              />
                            </svg>
                            <span>Copy</span>
                          </>
                        )}
                      </button>
                    </div>
                  )}

                  {/* Sources Accordion */}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="sources-container">
                      <button
                        onClick={() => toggleSources(msg.id)}
                        className="sources-toggle-btn"
                      >
                        <svg
                          width="12"
                          height="12"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                          style={{
                            transform: expandedSources[msg.id]
                              ? "rotate(180deg)"
                              : "none",
                            transition: "transform 0.2s",
                          }}
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth="2"
                            d="M19 9l-7 7-7-7"
                          />
                        </svg>
                        <span>
                          {expandedSources[msg.id] ? "Hide" : "View"}{" "}
                          {msg.sources.length} Verified Document{" "}
                          {msg.sources.length === 1 ? "Source" : "Sources"}
                        </span>
                      </button>

                      {expandedSources[msg.id] && (
                        <div className="source-cards-list">
                          {msg.sources.map((src, sIdx) => (
                            <div key={sIdx} className="source-card">
                              <div className="source-card-header">
                                <span className="source-page-badge">
                                  📄 Page {src.page || "N/A"}
                                </span>
                                <span className="source-chunk-id">
                                  {src.chunk_id}
                                </span>
                              </div>
                              <div className="source-excerpt">
                                &quot;{src.excerpt}&quot;
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))
        )}

        {/* Loading Indicator */}
        {isLoading && (
          <div className="message-row assistant">
            <div className="avatar-badge assistant">AI</div>
            <div className="message-bubble-wrapper">
              <div className="message-bubble">
                <div className="thinking-indicator">
                  <div className="spinner-dots">
                    <span />
                    <span />
                    <span />
                  </div>
                  <span>
                    Searching 194 vector chunks & synthesizing grounded answer...
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </main>

      {/* Floating Input Dock */}
      <footer className="input-dock-container">
        <div className="input-dock-inner">
          <div className="input-box-wrapper">
            <textarea
              ref={textareaRef}
              rows={1}
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything about the company knowledge base (e.g., founder, projects, head office)..."
              className="chat-input"
              disabled={isLoading}
            />

            <button
              onClick={() => handleSend()}
              disabled={isLoading || !input.trim()}
              className="btn-send"
              aria-label="Send message"
            >
              <svg
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2.5}
                  d="M14 5l7 7m0 0l-7 7m7-7H3"
                />
              </svg>
            </button>
          </div>

          <div className="input-dock-footer">
            <span>
              Press <strong>Enter ↵</strong> to send • <strong>Shift+Enter</strong> for newline
            </span>
            <div className="footer-features">
              <span className="footer-feature-item">🔒 100% Local Inference</span>
              <span className="footer-feature-item">•</span>
              <span className="footer-feature-item">📑 Exact Page Citations</span>
              <span className="footer-feature-item">•</span>
              <span className="footer-feature-item">⚡ Zero Hallucinations</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
