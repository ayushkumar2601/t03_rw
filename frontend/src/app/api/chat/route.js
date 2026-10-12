export async function POST(request) {
  try {
    const body = await request.json();
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
