(function () {
  var root = document.getElementById("chat-root");
  if (!root) return;
  var ZERO = "00000000-0000-0000-0000-000000000000";
  var csrf = root.dataset.csrf;
  var people = JSON.parse(document.getElementById("chat-people").textContent);
  var state = { convs: [], current: null, kind: "", lastId: 0, seen: {}, lastDay: "", file: null, sending: false, filter: "" };
  function $(id) { return document.getElementById(id); }
  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined && text !== null) e.textContent = text;
    return e;
  }
  function url(tpl, id) { return root.dataset[tpl].replace(ZERO, id); }
  function api(method, u, body) {
    var opts = { method: method, credentials: "same-origin", headers: { "X-CSRFToken": csrf } };
    if (body) opts.body = body;
    return fetch(u, opts).then(function (r) {
      return r.json().then(function (j) {
        if (!r.ok) throw new Error(j.error || "Request failed");
        return j;
      });
    });
  }
  function fmtTime(iso) { return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }); }
  function dayLabel(iso) {
    var d = new Date(iso), t = new Date(), y = new Date();
    y.setDate(t.getDate() - 1);
    if (d.toDateString() === t.toDateString()) return "Today";
    if (d.toDateString() === y.toDateString()) return "Yesterday";
    return d.toLocaleDateString([], { day: "numeric", month: "short", year: "numeric" });
  }
  function listTime(iso) {
    var d = new Date(iso);
    return d.toDateString() === new Date().toDateString() ? fmtTime(iso) : d.toLocaleDateString([], { day: "numeric", month: "short" });
  }

  function renderList() {
    var box = $("chat-list");
    box.innerHTML = "";
    var f = state.filter.toLowerCase();
    state.convs.forEach(function (c) {
      if (f && c.title.toLowerCase().indexOf(f) < 0) return;
      var row = el("div", "chat-row" + (c.id === state.current ? " active" : ""));
      row.appendChild(el("div", "chat-av", c.title.slice(0, 1).toUpperCase()));
      var mid = el("div", "chat-mid");
      mid.appendChild(el("div", "chat-name", c.title));
      mid.appendChild(el("div", "chat-prev", c.preview));
      row.appendChild(mid);
      var right = el("div", "chat-right");
      right.appendChild(el("div", "chat-time", listTime(c.time)));
      if (c.unread && c.id !== state.current) right.appendChild(el("span", "chat-unread", String(c.unread)));
      row.appendChild(right);
      row.onclick = function () { openConv(c.id); };
      box.appendChild(row);
    });
  }
  function loadConversations() {
    return api("GET", root.dataset.conversationsUrl).then(function (d) {
      state.convs = d.conversations;
      renderList();
    }).catch(function () {});
  }

  function buildMessage(m) {
    var wrap = el("div", "msg " + (m.mine ? "mine" : "theirs"));
    var bub = el("div", "bubble");
    if (!m.mine && state.kind !== "direct") bub.appendChild(el("div", "msg-sender", m.sender));
    if (m.kind === "image") {
      var a = el("a"); a.href = m.url; a.target = "_blank"; a.rel = "noopener";
      var img = el("img", "msg-img"); img.src = m.url; img.loading = "lazy"; img.alt = m.file_name;
      a.appendChild(img); bub.appendChild(a);
    } else if (m.kind === "video") {
      var v = el("video", "msg-video"); v.controls = true; v.preload = "metadata"; v.src = m.url;
      bub.appendChild(v);
    }
    if (m.text) bub.appendChild(el("div", "msg-text", m.text));
    bub.appendChild(el("div", "msg-time", fmtTime(m.created_at)));
    wrap.appendChild(bub);
    return wrap;
  }
  function appendMessages(list, forceScroll) {
    var box = $("chat-msgs");
    var nearBottom = box.scrollHeight - box.scrollTop - box.clientHeight < 120;
    list.forEach(function (m) {
      if (state.seen[m.id]) return;
      state.seen[m.id] = true;
      var lbl = dayLabel(m.created_at);
      if (lbl !== state.lastDay) {
        var day = el("div", "chat-day"); day.appendChild(el("span", "", lbl));
        box.appendChild(day);
        state.lastDay = lbl;
      }
      box.appendChild(buildMessage(m));
      if (m.id > state.lastId) state.lastId = m.id;
    });
    if (forceScroll || nearBottom) box.scrollTop = box.scrollHeight;
  }
  function fetchMessages(initial) {
    var id = state.current;
    if (!id) return Promise.resolve();
    return api("GET", url("messagesTpl", id) + "?after=" + state.lastId).then(function (d) {
      if (id !== state.current) return;
      state.kind = d.conversation.kind;
      $("chat-title").textContent = d.conversation.title;
      $("chat-sub").textContent = d.conversation.subtitle;
      appendMessages(d.messages, initial);
      if (d.messages.length) loadConversations();
    }).catch(function () {});
  }
  function openConv(id) {
    state.current = id; state.lastId = 0; state.seen = {}; state.lastDay = ""; state.kind = "";
    $("chat-msgs").innerHTML = "";
    $("chat-empty").style.display = "none";
    $("chat-thread").style.display = "flex";
    root.classList.add("thread-open");
    clearAttachment();
    renderList();
    fetchMessages(true).then(function () { $("chat-text").focus(); });
  }

  function clearAttachment() {
    state.file = null;
    $("chat-file").value = "";
    $("chat-attach").style.display = "none";
    $("chat-progress").style.width = "0";
  }
  $("chat-file").onchange = function () {
    var f = this.files[0];
    if (!f) return;
    state.file = f;
    $("chat-attach-name").textContent = f.name;
    $("chat-attach").style.display = "block";
  };
  $("chat-attach-x").onclick = clearAttachment;

  function autosize() {
    var t = $("chat-text");
    t.style.height = "auto";
    t.style.height = Math.min(t.scrollHeight, 120) + "px";
  }
  function send() {
    if (state.sending || !state.current) return;
    var text = $("chat-text").value.trim(), file = state.file;
    if (!text && !file) return;
    var fd = new FormData();
    fd.append("text", text);
    if (file) fd.append("file", file);
    state.sending = true;
    $("chat-send").disabled = true;
    var xhr = new XMLHttpRequest();
    xhr.open("POST", url("sendTpl", state.current));
    xhr.setRequestHeader("X-CSRFToken", csrf);
    xhr.upload.onprogress = function (e) {
      if (file && e.lengthComputable) $("chat-progress").style.width = Math.round(e.loaded * 100 / e.total) + "%";
    };
    xhr.onload = function () {
      state.sending = false;
      $("chat-send").disabled = false;
      var d = {};
      try { d = JSON.parse(xhr.responseText); } catch (e) {}
      if (xhr.status >= 200 && xhr.status < 300 && d.message) {
        $("chat-text").value = "";
        autosize();
        clearAttachment();
        appendMessages([d.message], true);
        loadConversations();
      } else {
        alert(d.error || "Could not send. Please try again.");
      }
    };
    xhr.onerror = function () {
      state.sending = false;
      $("chat-send").disabled = false;
      alert("Network error. Please try again.");
    };
    xhr.send(fd);
  }
  $("chat-send").onclick = send;
  $("chat-text").oninput = autosize;
  $("chat-text").onkeydown = function (e) {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
  };
  $("chat-back").onclick = function () {
    root.classList.remove("thread-open");
    state.current = null;
    $("chat-thread").style.display = "none";
    $("chat-empty").style.display = "";
    renderList();
  };
  $("chat-search").oninput = function () { state.filter = this.value; renderList(); };

  // ---- New chat / new group picker ----
  var mode = "";
  function openModal(m) {
    mode = m;
    $("chat-modal").style.display = "flex";
    $("chat-modal-title").textContent = m === "direct" ? "Start a chat" : "New group";
    $("chat-modal-name").style.display = m === "group" ? "block" : "none";
    $("chat-modal-name").value = "";
    $("chat-modal-ok").style.display = m === "group" ? "inline-block" : "none";
    var box = $("chat-modal-people");
    box.innerHTML = "";
    people.forEach(function (p) {
      var row = el("label", "chat-person");
      if (m === "group") {
        var cb = document.createElement("input");
        cb.type = "checkbox"; cb.value = p.id;
        row.appendChild(cb);
      }
      row.appendChild(el("span", "", p.name));
      row.appendChild(el("small", "", p.role));
      if (m === "direct") {
        row.onclick = function () {
          api("POST", root.dataset.directTpl.replace("/0/", "/" + p.id + "/")).then(function (d) {
            closeModal();
            loadConversations().then(function () { openConv(d.id); });
          }).catch(function (e) { alert(e.message); });
        };
      }
      box.appendChild(row);
    });
  }
  function closeModal() { $("chat-modal").style.display = "none"; }
  $("chat-new").onclick = function () { openModal("direct"); };
  $("chat-newgroup").onclick = function () { openModal("group"); };
  $("chat-modal-cancel").onclick = closeModal;
  $("chat-modal-ok").onclick = function () {
    var fd = new FormData();
    fd.append("name", $("chat-modal-name").value);
    var boxes = $("chat-modal-people").querySelectorAll("input:checked");
    for (var i = 0; i < boxes.length; i++) fd.append("members", boxes[i].value);
    api("POST", root.dataset.groupsUrl, fd).then(function (d) {
      closeModal();
      loadConversations().then(function () { openConv(d.id); });
    }).catch(function (e) { alert(e.message); });
  };

  // ---- Live updates: poll every few seconds while the tab is visible ----
  setInterval(function () { if (!document.hidden) fetchMessages(false); }, 3000);
  setInterval(function () { if (!document.hidden) loadConversations(); }, 6000);
  document.addEventListener("visibilitychange", function () {
    if (!document.hidden) { fetchMessages(false); loadConversations(); }
  });
  loadConversations().then(function () {
    var everyone = state.convs.filter(function (c) { return c.kind === "everyone"; })[0];
    if (everyone && window.innerWidth > 760) openConv(everyone.id);
  });
})();
