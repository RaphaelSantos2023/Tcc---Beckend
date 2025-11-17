// src/geminiService.js
export async function perguntarGemini(prompt) {

  const token = localStorage.getItem("token");
  const res = await fetch("http://localhost:5000/gemini/query", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    },
    body: JSON.stringify({ prompt })
  });

  const data = await res.json();
  return data;
}
