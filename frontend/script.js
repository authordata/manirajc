const API_BASE = "http://localhost:8000";
let token = null;
let activeSessionId = null;
let activeIsAi = false;

function setFlash(message, isError = false) {
  const el = document.getElementById("flashMessage");
  el.textContent = message;
  el.style.color = isError ? "#b91c1c" : "#4338ca";
}

function setAuthState(message) {
  document.getElementById("authState").textContent = message;
}

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
  if (el.textContent.trim() === "No conversation yet.") {
    el.textContent = "";
  }
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
    setFlash("Welcome to HearU! Account created.");
    setAuthState("Authenticated");
  } catch (err) {
    setFlash(`Register failed: ${err.message}`, true);
  }
};

document.getElementById("loginBtn").onclick = async () => {
  try {
    const data = await api("/auth/login", "POST", {
      email: document.getElementById("loginEmail").value,
      password: document.getElementById("loginPassword").value,
    });
    token = data.access_token;
    setFlash("Login successful.");
    setAuthState("Authenticated");
  } catch (err) {
    setFlash(`Login failed: ${err.message}`, true);
  }
};

document.getElementById("requestHumanBtn").onclick = async () => {
  try {
    const data = await api("/sessions/request", "POST", { cause: "Loneliness" });
    activeSessionId = data.session_id;
    activeIsAi = false;
    document.getElementById("sessionResult").innerText = `Human session #${data.session_id} (${data.status})`;
    setFlash("Connected to support flow.");
  } catch (err) {
    setFlash(`Could not request human session: ${err.message}`, true);
  }
};

document.getElementById("requestAiBtn").onclick = async () => {
  try {
    const data = await api("/sessions/request-ai", "POST", { cause: "Stress" });
    activeSessionId = data.session_id;
    activeIsAi = true;
    document.getElementById("sessionResult").innerText = `HearU AI session #${data.session_id} (${data.status})`;
    document.getElementById("chatOutput").textContent = "No conversation yet.";
    setFlash("HearU AI is ready for you.");
  } catch (err) {
    setFlash(`Could not request AI session: ${err.message}`, true);
  }
};

document.getElementById("sendAiMessageBtn").onclick = async () => {
  try {
    if (!activeSessionId || !activeIsAi) {
      setFlash("Start a HearU AI session first.", true);
      return;
    }
    const content = document.getElementById("chatInput").value.trim();
    if (!content) {
      setFlash("Please type a message.", true);
      return;
    }

    appendChat(`You: ${content}`);
    const data = await api(`/sessions/${activeSessionId}/ai-message`, "POST", { content });
    appendChat(`HearU AI: ${data.reply}`);
    document.getElementById("chatInput").value = "";
    setFlash("Message delivered.");
  } catch (err) {
    setFlash(`Could not send AI message: ${err.message}`, true);
  }
};
