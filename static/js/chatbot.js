document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const chatButton = document.getElementById('chat-button');
    const chatWidget = document.getElementById('chat-widget');
    const closeChat = document.getElementById('close-chat');
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const messagesContainer = document.getElementById('messages-container');
    const typingIndicator = document.getElementById('typing-indicator');
    
    // WebSocket connection
    let chatSocket = null;
    
    // Toggle chat widget
    chatButton.addEventListener('click', function() {
        chatWidget.classList.toggle('hidden');
        chatButton.classList.toggle('hidden');
        
        if (!chatWidget.classList.contains('hidden')) {
            connectWebSocket();
            messageInput.focus();
        } else {
            disconnectWebSocket();
        }
    });
    
    // Close chat widget
    closeChat.addEventListener('click', function() {
        chatWidget.classList.add('hidden');
        chatButton.classList.remove('hidden');
        disconnectWebSocket();
    });
    
    // Submit message
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const message = messageInput.value.trim();
        
        if (message && chatSocket && chatSocket.readyState === WebSocket.OPEN) {
            // Add user message to chat
            addMessage(message, 'user');
            
            // Send message to WebSocket
            chatSocket.send(JSON.stringify({
                'message': message
            }));
            
            // Clear input
            messageInput.value = '';
        }
    });
    
    // Connect to WebSocket
    function connectWebSocket() {
        if (chatSocket === null || chatSocket.readyState !== WebSocket.OPEN) {
            // Use wss:// for HTTPS sites, ws:// for HTTP
            const wsProtocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
            const wsUrl = wsProtocol + window.location.host + '/ws/chatbot/';
            
            chatSocket = new WebSocket(wsUrl);
            
            chatSocket.onopen = function(e) {
                console.log('WebSocket connection established');
            };
            
            chatSocket.onmessage = function(e) {
                const data = JSON.parse(e.data);
                
                // Handle different message types
                if (data.type === 'typing_indicator') {
                    if (data.is_typing) {
                        typingIndicator.classList.remove('hidden');
                    } else {
                        typingIndicator.classList.add('hidden');
                    }
                } else if (data.type === 'chatbot_response') {
                    // Hide typing indicator
                    typingIndicator.classList.add('hidden');
                    
                    // Add bot message
                    addMessage(data.message, 'bot');
                } else if (data.type === 'error') {
                    // Hide typing indicator
                    typingIndicator.classList.add('hidden');
                    
                    // Add error message
                    addMessage('Sorry, an error occurred. Please try again.', 'bot error');
                    console.error(data.message);
                }
            };
            
            chatSocket.onclose = function(e) {
                console.log('WebSocket connection closed');
            };
            
            chatSocket.onerror = function(e) {
                console.error('WebSocket error:', e);
                addMessage('Connection error. Please try again later.', 'bot error');
            };
        }
    }
    
    // Disconnect WebSocket
    function disconnectWebSocket() {
        if (chatSocket !== null) {
            chatSocket.close();
            chatSocket = null;
        }
    }
    
    // Add message to chat
    function addMessage(message, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', 'my-2');
        
        if (sender === 'user') {
            messageDiv.classList.add('text-right');
            messageDiv.innerHTML = `
                <div class="px-4 py-2 rounded-lg bg-grey-500 text-black inline-block max-w-3/4">
                    ${escapeHtml(message)}
                </div>
            `;
        } else {
            messageDiv.classList.add('bot-message');
            messageDiv.innerHTML = `
                <div class="px-4 py-2 rounded-lg bg-gray-200 inline-block max-w-3/4">
                    ${escapeHtml(message)}
                </div>
            `;
        }
        
        messagesContainer.appendChild(messageDiv);
        
        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    // Escape HTML to prevent XSS
    function escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});