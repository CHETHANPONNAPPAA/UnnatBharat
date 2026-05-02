let messageCount = 0;
let validCount = 0;
let invalidCount = 0;
const recentQueries = [];

function addMessage(text, sender) {
  const messages = document.getElementById("messages");

  const div = document.createElement("div");
  div.className = "msg " + sender;
  div.innerHTML = text;

  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
}

function updateStats() {
  document.getElementById("msgCount").innerText = "Messages: " + messageCount;
  updateAnalytics();
}

function updateAnalytics() {
  document.getElementById("analyticsMessageCount").innerText = messageCount;
  document.getElementById("analyticsValidCount").innerText = validCount;
  document.getElementById("analyticsInvalidCount").innerText = invalidCount;

  const recentElem = document.getElementById("analyticsRecentQueries");
  if (!recentQueries.length) {
    recentElem.innerText = "No queries yet.";
  } else {
    recentElem.innerHTML = recentQueries
      .slice(-5)
      .reverse()
      .map(query => `<div>• ${query}</div>`)
      .join("");
  }
}

function showTab(tabName) {
  const chatView = document.getElementById("chatView");
  const analyticsView = document.getElementById("analyticsView");
  const tabs = document.querySelectorAll(".nav-tab");

  if (tabName === "analytics") {
    chatView.classList.add("hidden");
    analyticsView.classList.remove("hidden");
  } else {
    chatView.classList.remove("hidden");
    analyticsView.classList.add("hidden");
  }

  tabs.forEach(tab => {
    tab.classList.toggle("active", tab.textContent.trim().toLowerCase() === tabName);
  });
}

async function sendMessage() {
  const input = document.getElementById("inputBox");
  const text = input.value.trim();

  if (!text) return;

  addMessage(text, "user");
  messageCount += 1;
  recentQueries.push(text);
  updateStats();

  input.value = "";

  
  addMessage("Typing...", "bot");

  let data;
  try {
    const res = await fetch("http://127.0.0.1:5000/chat", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({message: text})
    });

    if (!res.ok) {
      throw new Error(`Server error: ${res.status}`);
    }

    data = await res.json();
  } catch (error) {
    const typingElem = document.querySelector(".bot:last-child");
    if (typingElem) typingElem.remove();

    const errorDiv = document.createElement("div");
    errorDiv.className = "msg bot";
    errorDiv.innerHTML = "<div>Unable to reach backend. Please make sure the server is running.</div>";
    document.getElementById("messages").appendChild(errorDiv);
    document.getElementById("messages").scrollTop = document.getElementById("messages").scrollHeight;
    invalidCount += 1;
    updateAnalytics();
    return;
  }

  
  document.querySelector(".bot:last-child").remove();

  const messages = document.getElementById("messages");
  const div = document.createElement("div");
  div.className = "msg bot";

  if (data.reply) {
    div.innerHTML = data.reply;
  } else if (data.schemes && data.schemes.length) {
    let reply = "";
    data.schemes.forEach(s => {
      reply += `
        <div class="card">
          <b>${s.name}</b><br>
          ${s.details}<br>
          <b>Benefits:</b> ${s.benefits}<br>
          <b>Eligibility:</b> ${s.eligibility}<br>
          <b>Apply:</b> ${s.application}
        </div>
      `;
    });
    div.innerHTML = reply;
  } else {
    div.innerHTML = "<div>sorry input is invalid</div>";
  }

  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;

  const lastReplyText = div.textContent.toLowerCase();
  if (lastReplyText.includes("sorry input is invalid") || lastReplyText.includes("unable to reach backend")) {
    invalidCount += 1;
  } else {
    validCount += 1;
  }

  updateAnalytics();
}

function quickMsg(text) {
  document.getElementById("inputBox").value = text;
  sendMessage();
}

function newChat() {
  document.getElementById("messages").innerHTML = "";
  messageCount = 0;
  validCount = 0;
  invalidCount = 0;
  recentQueries.length = 0;
  updateStats();
  updateAnalytics();
}

showTab('chat');
document.getElementById("inputBox").addEventListener("keydown", function (e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault(); // prevent new line
    sendMessage();
  }
});