const CONVERSATIONAL_ANSWERS = {
  ok: "Understood! Feel free to ask any questions about Agarwal Constructions, our founder, projects, history, or policies.",
  okay: "Understood! Feel free to ask any questions about Agarwal Constructions, our founder, projects, history, or policies.",
  k: "Understood! Feel free to ask any questions about Agarwal Constructions.",
  fine: "Glad to hear! How can I assist you with Agarwal Constructions today?",
  sure: "Great! Feel free to ask any question about the company.",
  cool: "Happy to help! What would you like to know about Agarwal Constructions?",
  great: "Glad to hear! Feel free to ask any question about our projects or company profile.",
  "got it": "Understood! Feel free to ask anything else about Agarwal Constructions.",
  understood: "Perfect! Let me know if you need any other information from the knowledge base.",
  "sounds good": "Great! Let me know what you'd like to explore next.",
  hi: "Hello! I am the Agarwal Constructions AI Assistant. Ask me anything about our company's history, projects, leadership, or operations.",
  hello: "Hello! I am the Agarwal Constructions AI Assistant. Ask me anything about our company's history, projects, leadership, or operations.",
  hey: "Hey there! I am here to answer any questions about Agarwal Constructions.",
  thanks: "You're very welcome! Let me know if you need any other details.",
  "thank you": "You're very welcome! Let me know if you need any other details.",
  thx: "You're welcome! Let me know if you have any more questions.",
  "who are you": "I am the Agarwal Constructions Knowledge Base AI. I provide accurate, verified information about the company based on our official documentation.",
  "what can you do": "I can answer questions about Agarwal Constructions, including our founder Rajesh Agarwal, founding story, project portfolio, delivered square footage, head office contacts, and company policies.",
};

export async function POST(request) {
  try {
    const body = await request.json();
    const q = (body.question || "").trim().toLowerCase().replace(/[.!?]+$/, "");

    if (CONVERSATIONAL_ANSWERS[q]) {
      return Response.json({
        answer: CONVERSATIONAL_ANSWERS[q],
        status: "answered",
        sources: [],
        retrieval: { chunks_retrieved: 0, chunks_used: 0 },
      });
    }

    const response = await fetch("http://127.0.0.1:8000/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();
    return Response.json(data, { status: response.status });
  } catch (error) {
    return Response.json(
      {
        answer: "Failed to connect to RAG backend service. Please ensure the backend is running.",
        status: "error",
        error: error.message,
      },
      { status: 502 }
    );
  }
}
