"use client";

import { useEffect, useRef, useState } from "react";
import gsap from "gsap";

export default function FastshotLanding() {
  const [isExpanded, setIsExpanded] = useState(false);
  const [inputVal, setInputVal] = useState("");
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [expandedSourceIndex, setExpandedSourceIndex] = useState(null);

  const cardRef = useRef(null);
  const threadRef = useRef(null);
  const inputBarRef = useRef(null);
  const chatEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: no-preference)").matches
    ) {
      document.documentElement.classList.add("anim");
    }

    const timer = setTimeout(() => {
      document.documentElement.classList.remove("anim");
    }, 2600);

    return () => {
      clearTimeout(timer);
      document.documentElement.classList.remove("anim");
    };
  }, []);

  // GSAP Graceful Bounce Expanding Animation
  useEffect(() => {
    if (isExpanded && cardRef.current) {
      const isMobile = window.innerWidth <= 600;
      const targetWidth = isMobile
        ? Math.min(window.innerWidth - 32, 600)
        : Math.min(window.innerWidth * 0.95, 980);
      const targetHeight = isMobile
        ? Math.min(window.innerHeight * 0.84, 640)
        : Math.min(window.innerHeight * 0.85, 750);
      const startWidth = isMobile ? Math.min(window.innerWidth - 32, 516) : 708;
      const startHeight = 143;

      gsap.fromTo(
        cardRef.current,
        {
          width: startWidth,
          height: startHeight,
          borderRadius: 26,
          scale: 0.94,
          opacity: 0.92,
        },
        {
          width: targetWidth,
          height: targetHeight,
          borderRadius: isMobile ? 22 : 30,
          scale: 1,
          opacity: 1,
          duration: 0.8,
          ease: "back.out(1.45)", // Graceful bounce effect
          onComplete: () => {
            if (cardRef.current) {
              cardRef.current.style.width = "";
              cardRef.current.style.height = "";
            }
          },
        }
      );

      if (threadRef.current) {
        gsap.fromTo(
          threadRef.current,
          { opacity: 0, y: 22 },
          { opacity: 1, y: 0, duration: 0.45, delay: 0.16, ease: "power2.out" }
        );
      }

      if (inputBarRef.current) {
        gsap.fromTo(
          inputBarRef.current,
          { opacity: 0, y: 16, scale: 0.96 },
          {
            opacity: 1,
            y: 0,
            scale: 1,
            duration: 0.45,
            delay: 0.22,
            ease: "back.out(1.3)",
          }
        );
      }
    }
  }, [isExpanded]);

  useEffect(() => {
    if (isExpanded) {
      chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isLoading, isExpanded]);

  const handleSend = async (queryText) => {
    const q = (queryText !== undefined ? queryText : inputVal).trim();
    if (!q || isLoading) return;

    setInputVal("");
    if (!isExpanded) {
      setIsExpanded(true);
    }

    const userMsgId = Date.now();
    const assistantMsgId = userMsgId + 1;

    setMessages((prev) => [
      ...prev,
      { id: userMsgId, sender: "user", text: q },
      { id: assistantMsgId, sender: "assistant", text: "", isLoading: true },
    ]);
    setIsLoading(true);

    try {
      let res;
      try {
        res = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question: q }),
        });
      } catch {
        res = await fetch("http://127.0.0.1:8000/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question: q }),
        });
      }

      const data = await res.json();
      const answerText =
        data.answer || data.detail || "No response received from the knowledge base.";
      const sources = data.sources || [];

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMsgId
            ? {
                ...msg,
                text: answerText,
                sources: sources,
                isLoading: false,
              }
            : msg
        )
      );
    } catch (err) {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMsgId
            ? {
                ...msg,
                text: "Error communicating with the knowledge base service: " + err.message,
                isLoading: false,
              }
            : msg
        )
      );
    } finally {
      setIsLoading(false);
      setTimeout(() => {
        inputRef.current?.focus();
      }, 50);
    }
  };

  return (
    <div className="stage">
      <video
        className="stage-video"
        autoPlay
        muted
        loop
        playsInline
        src="https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260826_124724_bc041163-d651-425f-aea3-2acc1efc2c96.mp4"
      />

      <div className="frame">
        <main className={`hero ${isExpanded ? "has-expanded" : ""}`}>
          {!isExpanded && (
            <h1 className="h1">Ask anything about Agarwal Constructions.</h1>
          )}

          {!isExpanded ? (
            /* COLLAPSED INITIAL COMPOSER CARD */
            <form
              ref={cardRef}
              className="card"
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
            >
              <div className="ph-input-wrap">
                <input
                  type="text"
                  className="ph-input"
                  placeholder="Ask about company founder, history, projects, contact, or policies..."
                  value={inputVal}
                  onChange={(e) => setInputVal(e.target.value)}
                  autoFocus
                />
              </div>

              <div className="tools">
                <div className="chips">
                  <button
                    type="button"
                    className="chip"
                    onClick={() =>
                      handleSend("Who is the founder of Agarwal Constructions?")
                    }
                  >
                    <svg
                      className="chip-icon"
                      style={{ width: "calc(14 * var(--u))", height: "auto" }}
                      viewBox="0 0 16 13"
                      fill="currentColor"
                    >
                      <path d="M1 2.5A1.5 1.5 0 0 1 2.5 1h11A1.5 1.5 0 0 1 15 2.5v7A1.5 1.5 0 0 1 13.5 11H9.2v1.2h1.6a.6.6 0 0 1 0 1.2H5.2a.6.6 0 0 1 0-1.2h1.6V11H2.5A1.5 1.5 0 0 1 1 9.5v-7z" />
                    </svg>
                    <span>Founder &amp; History</span>
                  </button>

                  <button
                    type="button"
                    className="chip"
                    onClick={() =>
                      handleSend(
                        "In what year was Agarwal Constructions founded and what was the initial vision?"
                      )
                    }
                  >
                    <svg
                      className="chip-icon"
                      style={{ width: "calc(11 * var(--u))", height: "auto" }}
                      viewBox="0 0 24 36"
                      fill="currentColor"
                    >
                      <path d="M0 6C0 2.686 2.686 0 6 0h6v12H6C2.686 12 0 9.314 0 6z" />
                      <path d="M12 0h6c3.314 0 6 2.686 6 6s-2.686 6-6 6h-6V0z" />
                      <path d="M0 18c0-3.314 2.686-6 6-6h6v12H6c-3.314 0-6-2.686-6-6z" />
                      <path d="M12 18a6 6 0 1 0 12 0 6 6 0 0 0-12 0z" />
                      <path d="M0 30c0-3.314 2.686-6 6-6h6v6a6 6 0 0 1-6 6c-3.314 0-6-2.686-6-6z" />
                    </svg>
                    <span>Founded in 1995</span>
                  </button>

                  <button
                    type="button"
                    className="chip"
                    onClick={() =>
                      handleSend(
                        "What is the head office address and contact email for Agarwal Constructions?"
                      )
                    }
                  >
                    <svg
                      className="chip-icon"
                      style={{ width: "calc(11.5 * var(--u))", height: "auto" }}
                      viewBox="0 0 14 14"
                      fill="currentColor"
                    >
                      <path d="M7 0C7 3.866 10.134 7 14 7C10.134 7 7 10.134 7 14C7 10.134 3.866 7 0 7C3.866 7 7 3.866 7 0Z" />
                    </svg>
                    <span>Head Office &amp; Contact</span>
                  </button>
                </div>

                <div className="right">
                  <button type="button" className="model">
                    <span>Llama 3 (Ollama)</span>
                    <svg
                      className="model-chev"
                      viewBox="0 0 7 4"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <path d="M1 1l2.5 2.5L6 1" />
                    </svg>
                  </button>

                  <button type="button" className="attach" aria-label="Attach document">
                    <svg
                      className="attach-icon"
                      viewBox="0 0 20 20"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1.7"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <path d="M15.172 7L8.1 14.071a3.5 3.5 0 0 1-4.95-4.95l7.072-7.07a2.333 2.333 0 0 1 3.3 3.3L6.45 12.422a1.167 1.167 0 0 1-1.65-1.65l6.364-6.364" />
                    </svg>
                  </button>

                  <button
                    type="submit"
                    className="send"
                    aria-label="Search Knowledge Base"
                  >
                    <svg className="send-arrow" viewBox="0 0 12 14" fill="#ffffff">
                      <path d="M6 1.2a.8.8 0 0 0-.57.24L1.24 5.63a.8.8 0 1 0 1.13 1.13L5.2 3.93V12.8a.8.8 0 1 0 1.6 0V3.93l2.83 2.83a.8.8 0 0 0 1.13-1.13L6.57 1.44A.8.8 0 0 0 6 1.2z" />
                    </svg>
                  </button>
                </div>
              </div>
            </form>
          ) : (
            /* EXPANDED CHAT BOX (WITH GSAP BOUNCE ANIMATION, NO TOPBAR, NO MIC) */
            <div ref={cardRef} className="card expanded">
              <div ref={threadRef} className="chat-thread">
                {messages.map((m, idx) => {
                  if (m.sender === "user") {
                    return (
                      <div key={m.id || idx} className="msg-user-row">
                        <div className="msg-user-bubble">{m.text}</div>
                        <svg
                          className="user-avatar-icon"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="1.8"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        >
                          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                          <circle cx="12" cy="7" r="4" />
                        </svg>
                      </div>
                    );
                  }

                  return (
                    <div key={m.id || idx} className="msg-assistant-row">
                      <div className="assistant-orb" />
                      <div className="msg-assistant-bubble">
                        {m.isLoading ? (
                          <div className="typing-dots">
                            <span className="dot" />
                            <span className="dot" />
                            <span className="dot" />
                          </div>
                        ) : (
                          <>
                            <div>{m.text}</div>
                            {m.sources && m.sources.length > 0 && (
                              <div className="sources-container">
                                {m.sources.map((s, sIdx) => (
                                  <button
                                    key={sIdx}
                                    type="button"
                                    className="source-badge"
                                    onClick={() =>
                                      setExpandedSourceIndex(
                                        expandedSourceIndex === `${idx}-${sIdx}`
                                          ? null
                                          : `${idx}-${sIdx}`
                                      )
                                    }
                                  >
                                    <span>📄 Page {s.page}</span>
                                    {s.chunk_id && (
                                      <span style={{ opacity: 0.65 }}>
                                        · {s.chunk_id}
                                      </span>
                                    )}
                                  </button>
                                ))}
                              </div>
                            )}
                            {expandedSourceIndex &&
                              expandedSourceIndex.startsWith(`${idx}-`) && (
                                <div
                                  style={{
                                    marginTop: "8px",
                                    padding: "8px 12px",
                                    borderRadius: "8px",
                                    background: "rgba(0,0,0,0.35)",
                                    fontSize: "12px",
                                    color: "#cbd5e1",
                                    lineHeight: 1.4,
                                    border: "1px solid rgba(255,255,255,0.08)",
                                  }}
                                >
                                  <strong>Excerpt from source:</strong>
                                  <p style={{ marginTop: "4px" }}>
                                    {
                                      m.sources[
                                        parseInt(
                                          expandedSourceIndex.split("-")[1],
                                          10
                                        )
                                      ]?.excerpt
                                    }
                                  </p>
                                </div>
                              )}
                          </>
                        )}
                      </div>
                    </div>
                  );
                })}
                <div ref={chatEndRef} />
              </div>

              {/* BOTTOM INPUT BAR */}
              <div ref={inputBarRef} className="chat-input-bar-container">
                <form
                  className="chat-input-pill"
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleSend();
                  }}
                >
                  <input
                    ref={inputRef}
                    type="text"
                    className="pill-text-input"
                    placeholder="Ask anything about Agarwal Constructions..."
                    value={inputVal}
                    onChange={(e) => setInputVal(e.target.value)}
                    disabled={isLoading}
                    autoFocus
                  />

                  <button
                    type="submit"
                    className="pill-send-btn"
                    aria-label="Send query"
                    disabled={isLoading}
                  >
                    <svg
                      className="pill-send-arrow"
                      viewBox="0 0 12 14"
                      fill="currentColor"
                    >
                      <path d="M6 1.2a.8.8 0 0 0-.57.24L1.24 5.63a.8.8 0 1 0 1.13 1.13L5.2 3.93V12.8a.8.8 0 1 0 1.6 0V3.93l2.83 2.83a.8.8 0 0 0 1.13-1.13L6.57 1.44A.8.8 0 0 0 6 1.2z" />
                    </svg>
                  </button>
                </form>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
