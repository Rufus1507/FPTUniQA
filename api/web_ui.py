"""Giao diện Web Chat trực quan cho hệ thống FPTUniQA."""

CHAT_HTML_PAGE = """<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FPTUniQA - Trợ lý Quy chế & Đào tạo Đại học FPT</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #F27024;
            --primary-hover: #D65A15;
            --bg: #F8FAFC;
            --card-bg: #FFFFFF;
            --text-main: #0F172A;
            --text-muted: #64748B;
            --border: #E2E8F0;
            --bot-bubble: #F1F5F9;
            --user-bubble: linear-gradient(135deg, #F27024, #EA580C);
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
        body { background-color: var(--bg); color: var(--text-main); display: flex; height: 100vh; overflow: hidden; }

        /* Sidebar gợi ý câu hỏi test */
        .sidebar {
            width: 320px;
            background: var(--card-bg);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            padding: 20px;
            flex-shrink: 0;
        }
        .brand {
            display: flex;
            align-items: center;
            gap: 12px;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border);
            margin-bottom: 16px;
        }
        .logo {
            width: 42px;
            height: 42px;
            background: var(--primary);
            color: #fff;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
            font-weight: 700;
        }
        .brand h2 { font-size: 18px; font-weight: 700; color: #1E293B; }
        .brand p { font-size: 12px; color: var(--text-muted); }

        .btn-new {
            background: #EFF6FF;
            color: #1D4ED8;
            border: 1px solid #BFDBFE;
            padding: 10px 14px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            transition: all 0.2s;
        }
        .btn-new:hover { background: #DBEAFE; }

        .session-btn-group {
            display: flex;
            gap: 6px;
            margin-bottom: 16px;
        }
        .session-btn-group .btn-new {
            flex: 1.2;
            margin-bottom: 0;
            padding: 9px 8px;
            font-size: 12px;
        }
        .btn-save {
            flex: 1;
            background: #ECFDF5;
            color: #059669;
            border: 1px solid #A7F3D0;
            padding: 9px 8px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 4px;
            font-size: 12px;
            transition: all 0.2s;
        }
        .btn-save:hover { background: #D1FAE5; transform: translateY(-1px); }
        .btn-save.btn-secondary {
            background: #EEF2FF;
            color: #4F46E5;
            border: 1px solid #C7D2FE;
        }
        .btn-save.btn-secondary:hover { background: #E0E7FF; }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .btn-save-sm {
            background: #10B981;
            color: #FFF;
            border: none;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.2s;
        }
        .btn-save-sm:hover { background: #059669; transform: translateY(-1px); }
        .btn-save-sm.btn-secondary {
            background: #4F46E5;
        }
        .btn-save-sm.btn-secondary:hover { background: #4338CA; }

        .section-title {
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-muted);
            margin-bottom: 10px;
            font-weight: 600;
        }
        .sample-list {
            list-style: none;
            overflow-y: auto;
            flex-grow: 1;
            padding-right: 4px;
        }
        .sample-item {
            background: #F8FAFC;
            border: 1px solid var(--border);
            padding: 10px 12px;
            border-radius: 8px;
            margin-bottom: 8px;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s;
            line-height: 1.4;
        }
        .sample-item:hover {
            background: #FFF7ED;
            border-color: #FDBA74;
            color: #C2410C;
            transform: translateY(-1px);
        }
        .sample-badge {
            display: inline-block;
            font-size: 10px;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 600;
            margin-bottom: 4px;
        }
        .badge-syllabus { background: #DCFCE7; color: #15803D; }
        .badge-textbook { background: #E0E7FF; color: #4338CA; }
        .badge-multi { background: #FEF3C7; color: #B45309; }

        /* Main Chat Area */
        .chat-container {
            flex-grow: 1;
            display: flex;
            flex-direction: column;
            background: #F8FAFC;
        }
        .chat-header {
            padding: 16px 24px;
            background: var(--card-bg);
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .chat-header h3 { font-size: 16px; font-weight: 600; }
        .session-tag {
            font-size: 12px;
            background: #F1F5F9;
            padding: 4px 10px;
            border-radius: 20px;
            color: var(--text-muted);
        }

        .chat-messages {
            flex-grow: 1;
            overflow-y: auto;
            padding: 24px;
            display: flex;
            flex-direction: column;
            gap: 18px;
        }
        .message {
            display: flex;
            gap: 12px;
            max-width: 80%;
            animation: fadeIn 0.25s ease-out;
        }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }

        .message.user { align-self: flex-end; flex-direction: row-reverse; }
        .message.bot { align-self: flex-start; }

        .avatar {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 14px;
            flex-shrink: 0;
        }
        .user .avatar { background: #1E293B; color: #FFF; }
        .bot .avatar { background: var(--primary); color: #FFF; }

        .bubble {
            padding: 14px 18px;
            border-radius: 14px;
            font-size: 14px;
            line-height: 1.6;
            white-space: pre-wrap;
            word-break: break-word;
        }
        .user .bubble {
            background: var(--user-bubble);
            color: #FFF;
            border-bottom-right-radius: 4px;
            box-shadow: 0 2px 8px rgba(242, 112, 36, 0.2);
        }
        .bot .bubble {
            background: var(--card-bg);
            color: var(--text-main);
            border: 1px solid var(--border);
            border-bottom-left-radius: 4px;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
        }

        .meta-info {
            display: flex;
            gap: 8px;
            align-items: center;
            margin-top: 8px;
            font-size: 11px;
            color: var(--text-muted);
        }
        .route-pill {
            background: #E2E8F0;
            color: #334155;
            padding: 2px 8px;
            border-radius: 12px;
            font-weight: 600;
        }
        .route-pill.structured { background: #DCFCE7; color: #166534; }
        .route-pill.rag { background: #DBEAFE; color: #1E40AF; }
        .route-pill.ood { background: #FEE2E2; color: #991B1B; }

        .citations {
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px dashed var(--border);
            font-size: 12px;
        }
        .citations summary {
            cursor: pointer;
            color: #2563EB;
            font-weight: 600;
        }

        /* Input Bar */
        .chat-input-area {
            padding: 16px 24px;
            background: var(--card-bg);
            border-top: 1px solid var(--border);
            display: flex;
            gap: 12px;
        }
        .chat-input {
            flex-grow: 1;
            padding: 12px 18px;
            border: 1px solid var(--border);
            border-radius: 10px;
            font-size: 14px;
            outline: none;
            transition: border-color 0.2s;
        }
        .chat-input:focus { border-color: var(--primary); }
        .btn-send {
            background: var(--primary);
            color: #FFF;
            border: none;
            padding: 12px 24px;
            border-radius: 10px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.2s;
        }
        .btn-send:hover { background: var(--primary-hover); }
        .btn-send:disabled { background: #CBD5E1; cursor: not-allowed; }

        .loading-dots span {
            animation: blink 1.4s infinite both;
            font-size: 20px;
            line-height: 10px;
        }
        .loading-dots span:nth-child(2) { animation-delay: .2s; }
        .loading-dots span:nth-child(3) { animation-delay: .4s; }
        @keyframes blink { 0% { opacity: .2; } 20% { opacity: 1; } 100% { opacity: .2; } }
    </style>
</head>
<body>

    <!-- Sidebar với các câu hỏi mẫu có thể click ngay -->
    <div class="sidebar">
        <div class="brand">
            <div class="logo">F</div>
            <div>
                <h2>FPTUniQA</h2>
                <p>Hệ thống Học vụ & Môn học</p>
            </div>
        </div>

        <div class="session-btn-group">
            <button class="btn-new" onclick="startNewSession()" title="Tạo một phiên hội thoại hoàn toàn mới">
                <span>➕ Phiên mới</span>
            </button>
            <button class="btn-save" onclick="exportSessionJSON()" title="Lưu toàn bộ phiên này về máy (JSON)">
                <span>💾 Lưu JSON</span>
            </button>
            <button class="btn-save btn-secondary" onclick="exportSessionMarkdown()" title="Lưu báo cáo Markdown">
                <span>📝 Lưu MD</span>
            </button>
        </div>

        <div class="section-title">Câu hỏi Test Mẫu (Click để hỏi)</div>
        <div class="sample-list">
            <div class="sample-item" onclick="askQuestion('Môn PRF192 học những gì?')">
                <span class="sample-badge badge-syllabus">Nội dung học</span>
                <div>Môn PRF192 học những gì?</div>
            </div>
            <div class="sample-item" onclick="askQuestion('Giáo trình môn PRO192 là sách nào?')">
                <span class="sample-badge badge-textbook">Giáo trình</span>
                <div>Giáo trình môn PRO192 là sách nào?</div>
            </div>
            <div class="sample-item" onclick="askQuestion('Môn CSD201 học về những nội dung gì?')">
                <span class="sample-badge badge-syllabus">Nội dung học</span>
                <div>Môn CSD201 học về những nội dung gì?</div>
            </div>
            <div class="sample-item" onclick="askQuestion('Giáo trình môn MKT101 của ai viết?')">
                <span class="sample-badge badge-textbook">Giáo trình</span>
                <div>Giáo trình môn MKT101 của ai viết?</div>
            </div>
            <div class="sample-item" onclick="askQuestion('Môn DBI202 học những gì?')">
                <span class="sample-badge badge-syllabus">Nội dung học</span>
                <div>Môn DBI202 học những gì?</div>
            </div>
            <div class="sample-item" onclick="askQuestion('Môn Võ Vovinam 1 VOV114 học những gì?')">
                <span class="sample-badge badge-syllabus">Nội dung học</span>
                <div>Môn Võ Vovinam 1 VOV114 học những gì?</div>
            </div>
            <div class="sample-item" onclick="askQuestion('Môn PRO192 yêu cầu môn tiên quyết nào?')">
                <span class="sample-badge badge-multi">Tiên quyết</span>
                <div>Môn PRO192 yêu cầu môn tiên quyết nào?</div>
            </div>
            <div class="sample-item" onclick="askQuestion('Thế sau khi qua môn đó thì học tiếp môn nào?')">
                <span class="sample-badge badge-multi">Đa lượt</span>
                <div>Thế sau khi qua môn đó thì học tiếp môn nào?</div>
            </div>
            <div class="sample-item" onclick="askQuestion('Học phí ngành AI khóa 2026 tại Hà Nội là bao nhiêu?')">
                <span class="sample-badge badge-multi">Học phí</span>
                <div>Học phí ngành AI khóa 2026 tại Hà Nội là bao nhiêu?</div>
            </div>
            <div class="sample-item" onclick="askQuestion('Cách làm món phở bò ngon?')">
                <span class="sample-badge" style="background:#FEE2E2; color:#B91C1C;">OOD</span>
                <div>Cách làm món phở bò ngon?</div>
            </div>
        </div>
    </div>

    <!-- Main Chat Container -->
    <div class="chat-container">
        <div class="chat-header">
            <h3>💬 Hỏi Đáp Trực Tiếp Quy Chế & Đào Tạo</h3>
            <div class="header-actions">
                <span class="session-tag" id="sessionTag">Session: khởi tạo...</span>
                <button class="btn-save-sm" onclick="exportSessionJSON()" title="Lưu toàn bộ phiên hội thoại này về máy (JSON)">💾 Lưu Session (JSON)</button>
                <button class="btn-save-sm btn-secondary" onclick="exportSessionMarkdown()" title="Lưu báo cáo dạng Markdown">📝 Báo cáo (MD)</button>
            </div>
        </div>

        <div class="chat-messages" id="chatMessages">
            <div class="message bot">
                <div class="avatar">F</div>
                <div>
                    <div class="bubble">Xin chào bạn! Tôi là trợ lý giải đáp học vụ và môn học Đại học FPT. Bạn có thể hỏi tôi về nội dung môn học, giáo trình, điều kiện tiên quyết, học phí hoặc quy chế đào tạo. Hãy chọn một câu hỏi mẫu bên trái hoặc nhập câu hỏi bên dưới nhé!</div>
                </div>
            </div>
        </div>

        <div class="chat-input-area">
            <input type="text" id="userInput" class="chat-input" placeholder="Nhập câu hỏi học vụ hoặc mã môn học (ví dụ: Môn PRF192 học những gì?)..." onkeypress="handleKeyPress(event)">
            <button id="sendBtn" class="btn-send" onclick="sendQuery()">Gửi câu hỏi</button>
        </div>
    </div>

    <script>
        let sessionId = 'session_' + Math.random().toString(36).substring(2, 9);
        let currentSessionHistory = [];
        document.getElementById('sessionTag').innerText = 'Session: ' + sessionId;

        function startNewSession() {
            sessionId = 'session_' + Math.random().toString(36).substring(2, 9);
            currentSessionHistory = []; // Reset hoàn toàn phiên mới, cô lập với phiên cũ
            document.getElementById('sessionTag').innerText = 'Session: ' + sessionId;
            const chat = document.getElementById('chatMessages');
            chat.innerHTML = `
                <div class="message bot">
                    <div class="avatar">F</div>
                    <div>
                        <div class="bubble">Đã bắt đầu phiên hội thoại mới (${sessionId}). Toàn bộ truy vấn của phiên trước đã được tách biệt độc lập. Mời bạn đặt câu hỏi!</div>
                    </div>
                </div>
            `;
        }

        function askQuestion(q) {
            document.getElementById('userInput').value = q;
            sendQuery();
        }

        function handleKeyPress(e) {
            if (e.key === 'Enter') sendQuery();
        }

        async function sendQuery() {
            const input = document.getElementById('userInput');
            const btn = document.getElementById('sendBtn');
            const query = input.value.trim();
            if (!query) return;

            // Render tin nhắn của User
            renderMessage(query, 'user');
            input.value = '';
            input.disabled = true;
            btn.disabled = true;

            // Render tin nhắn loading của Bot
            const loadingId = 'loading_' + Date.now();
            renderLoading(loadingId);

            try {
                const response = await fetch('/api/v1/query', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: query, session_id: sessionId })
                });

                const data = await response.json();
                removeElement(loadingId);

                if (response.ok) {
                    // Lưu lại toàn bộ thông tin query, truy vấn và answer của lượt này vào session hiện tại
                    const turnData = {
                        turn: currentSessionHistory.length + 1,
                        session_id: sessionId,
                        timestamp: new Date().toISOString(),
                        query: query,
                        rewritten_query: data.rewritten_query || query,
                        route: data.route || 'unknown',
                        answer: data.answer || '',
                        citations: data.citations || []
                    };
                    currentSessionHistory.push(turnData);

                    renderBotResponse(data);
                } else {
                    renderMessage('Xin lỗi, hệ thống gặp lỗi khi xử lý câu hỏi: ' + (data.detail || 'Không xác định'), 'bot');
                }
            } catch (err) {
                removeElement(loadingId);
                renderMessage('Không thể kết nối đến máy chủ. Vui lòng kiểm tra lại dịch vụ.', 'bot');
            } finally {
                input.disabled = false;
                btn.disabled = false;
                input.focus();
            }
        }

        function exportSessionJSON() {
            if (!currentSessionHistory || currentSessionHistory.length === 0) {
                alert(`Phiên hiện tại (${sessionId}) chưa có câu hỏi nào để lưu! Vui lòng đặt câu hỏi trước khi lưu.`);
                return;
            }

            const exportPayload = {
                session_id: sessionId,
                exported_at: new Date().toISOString(),
                total_turns: currentSessionHistory.length,
                system: "FPTUniQA - Assistant Đào tạo & Môn học Đại học FPT",
                history: currentSessionHistory
            };

            const blob = new Blob([JSON.stringify(exportPayload, null, 2)], { type: 'application/json;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            const dateStr = new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-');
            a.href = url;
            a.download = `FPTUniQA_${sessionId}_${dateStr}.json`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(url);
        }

        function exportSessionMarkdown() {
            if (!currentSessionHistory || currentSessionHistory.length === 0) {
                alert(`Phiên hiện tại (${sessionId}) chưa có câu hỏi nào để lưu!`);
                return;
            }

            const lines = [
                `# Nhật Ký Phiên Hội Thoại FPTUniQA`,
                ``,
                `- **Mã Phiên (Session ID):** \`${sessionId}\``,
                `- **Thời gian xuất file:** ${new Date().toLocaleString('vi-VN')}`,
                `- **Tổng số lượt hỏi đáp:** ${currentSessionHistory.length}`,
                ``,
                `---`,
                ``
            ];

            currentSessionHistory.forEach((item) => {
                lines.push(`### Lượt ${item.turn}: ${item.query}`);
                lines.push(``);
                lines.push(`- **Thời gian:** ${new Date(item.timestamp).toLocaleTimeString('vi-VN')}`);
                lines.push(`- **Định tuyến (Route):** \`${item.route}\``);
                if (item.rewritten_query && item.rewritten_query !== item.query) {
                    lines.push(`- **Câu hỏi viết lại:** *"${item.rewritten_query}"*`);
                }
                lines.push(``);
                lines.push(`#### 🤖 Trả lời của LLM:`);
                lines.push(``);
                lines.push(item.answer);
                lines.push(``);
                if (item.citations && item.citations.length > 0) {
                    lines.push(`#### 📚 Nguồn trích dẫn:`);
                    item.citations.forEach(c => {
                        lines.push(`- [${c.doc_id}] ${c.title}`);
                    });
                    lines.push(``);
                }
                lines.push(`---`);
                lines.push(``);
            });

            const blob = new Blob([lines.join('\\n')], { type: 'text/markdown;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            const dateStr = new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-');
            a.href = url;
            a.download = `FPTUniQA_${sessionId}_${dateStr}.md`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(url);
        }

        function renderMessage(text, role) {
            const chat = document.getElementById('chatMessages');
            const msg = document.createElement('div');
            msg.className = 'message ' + role;
            msg.innerHTML = `
                <div class="avatar">${role === 'user' ? 'U' : 'F'}</div>
                <div><div class="bubble">${escapeHtml(text)}</div></div>
            `;
            chat.appendChild(msg);
            chat.scrollTop = chat.scrollHeight;
        }

        function renderBotResponse(data) {
            const chat = document.getElementById('chatMessages');
            const msg = document.createElement('div');
            msg.className = 'message bot';

            let routeClass = 'structured';
            if (data.route === 'rag_pipeline') routeClass = 'rag';
            else if (data.route === 'ood') routeClass = 'ood';

            let citationsHtml = '';
            if (data.citations && data.citations.length > 0) {
                citationsHtml = `
                    <details class="citations">
                        <summary>📚 Nguồn trích dẫn (${data.citations.length})</summary>
                        <ul style="margin: 6px 0 0 16px;">
                            ${data.citations.map(c => `<li><strong>[${escapeHtml(c.doc_id)}]</strong> ${escapeHtml(c.title)}</li>`).join('')}
                        </ul>
                    </details>
                `;
            }

            let rewrittenHtml = '';
            if (data.rewritten_query && data.rewritten_query !== data.original_query) {
                rewrittenHtml = `<span>• Viết lại: <em>"${escapeHtml(data.rewritten_query)}"</em></span>`;
            }

            msg.innerHTML = `
                <div class="avatar">F</div>
                <div>
                    <div class="bubble">${escapeHtml(data.answer)}</div>
                    <div class="meta-info">
                        <span class="route-pill ${routeClass}">${escapeHtml(data.route || 'unknown')}</span>
                        ${rewrittenHtml}
                    </div>
                    ${citationsHtml}
                </div>
            `;
            chat.appendChild(msg);
            chat.scrollTop = chat.scrollHeight;
        }

        function renderLoading(id) {
            const chat = document.getElementById('chatMessages');
            const msg = document.createElement('div');
            msg.className = 'message bot';
            msg.id = id;
            msg.innerHTML = `
                <div class="avatar">F</div>
                <div><div class="bubble loading-dots">Đang xử lý <span>.</span><span>.</span><span>.</span></div></div>
            `;
            chat.appendChild(msg);
            chat.scrollTop = chat.scrollHeight;
        }

        function removeElement(id) {
            const el = document.getElementById(id);
            if (el) el.remove();
        }

        function escapeHtml(str) {
            if (!str) return '';
            return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
        }
    </script>
</body>
</html>
"""
