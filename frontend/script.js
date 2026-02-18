const API_BASE = "http://localhost:8000";
let token = null;
let activeSessionId = null;
let activeIsAi = false;

async function api(path, method = "GET", body = null) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : null,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || "Request failed");
  }
  return res.json();
}

function appendChat(line) {
  const el = document.getElementById("chatOutput");
  el.textContent += `${line}\n`;
}

document.getElementById("registerBtn").onclick = async () => {
  try {
    const data = await api("/auth/register", "POST", {
      email: document.getElementById("email").value,
      password: document.getElementById("password").value,
      display_name: document.getElementById("displayName").value,
      role: document.getElementById("role").value,
      is_anonymous: true,
    });
    token = data.access_token;
    alert("Registered successfully");
  } catch (err) {
    alert(`Register failed: ${err.message}`);
  }
};

document.getElementById("loginBtn").onclick = async () => {
  try {
    const data = await api("/auth/login", "POST", {
      email: document.getElementById("loginEmail").value,
      password: document.getElementById("loginPassword").value,
    });
    token = data.access_token;
    alert("Login successful");
  } catch (err) {
    alert(`Login failed: ${err.message}`);
  }
};

document.getElementById("requestHumanBtn").onclick = async () => {
  try {
    const data = await api("/sessions/request", "POST", { cause: "Loneliness" });
    activeSessionId = data.session_id;
    activeIsAi = false;
    document.getElementById("sessionResult").innerText = `Human session #${data.session_id} (${data.status})`;
  } catch (err) {
    alert(`Could not request human session: ${err.message}`);
  }
};

document.getElementById("requestAiBtn").onclick = async () => {
  try {
    const data = await api("/sessions/request-ai", "POST", { cause: "Stress" });
    activeSessionId = data.session_id;
    activeIsAi = true;
    document.getElementById("sessionResult").innerText = `AI session #${data.session_id} (${data.status})`;
    document.getElementById("chatOutput").textContent = "";
  } catch (err) {
    alert(`Could not request AI session: ${err.message}`);
  }
};

document.getElementById("sendAiMessageBtn").onclick = async () => {
  try {
    if (!activeSessionId || !activeIsAi) {
      alert("Start an AI session first.");
      return;
    }
    const content = document.getElementById("chatInput").value;
    appendChat(`You: ${content}`);
    const data = await api(`/sessions/${activeSessionId}/ai-message`, "POST", { content });
    appendChat(`AI: ${data.reply}`);
    document.getElementById("chatInput").value = "";
  } catch (err) {
    alert(`Could not send AI message: ${err.message}`);
  }
};
