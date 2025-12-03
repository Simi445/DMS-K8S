import React, { useState, useEffect, useRef } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import io, { Socket } from 'socket.io-client';

interface Admin {
  id: string;
  username: string;
  name: string;
  is_online: boolean;
}

interface Message {
  id: string;
  sender_id: string;
  receiver_id: string;
  content: string;
  timestamp: string;
  is_read: boolean;
  message_type: string;
}

interface ChatWindowProps {
  userId: string;
  userName: string;
  onClose: () => void;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({ userId, userName, onClose }) => {
  const [admins, setAdmins] = useState<Admin[]>([]);
  const [selectedAdmin, setSelectedAdmin] = useState<Admin | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [otherUserTyping, setOtherUserTyping] = useState(false);
  const [chatSessionId, setChatSessionId] = useState<string>('');
  const [isMinimized, setIsMinimized] = useState(false);
  const [socket, setSocket] = useState<Socket | null>(null);
  const [chatMode, setChatMode] = useState<'admin' | 'ai'>('admin');
  const [isAiThinking, setIsAiThinking] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const socketConnection = io('/', {
      path: '/socket.io',
      transports: ['polling']
    });

    socketConnection.on('connect', () => {
      console.log('Socket.IO connected!', socketConnection.id);
    });

    socketConnection.on('connect_error', (error) => {
      console.error('Socket.IO connection error:', error);
    });

    socketConnection.on('disconnect', (reason) => {
      console.log('Socket.IO disconnected:', reason);
    });

    setSocket(socketConnection);

    return () => {
      socketConnection.disconnect();
    };
  }, []);

  useEffect(() => {
    if (chatMode === 'admin') {
      fetchAdmins();
    }
  }, [chatMode]);

  useEffect(() => {
    if (selectedAdmin && socket && chatMode === 'admin') {
      createChatSession();
    }
  }, [selectedAdmin, socket, chatMode]);

  useEffect(() => {
    if (!socket) return;

    socket.on('new_message', (message: Message) => {
      setMessages(prev => [...prev, message]);
    });

    socket.on('typing_started', (data: { user_id: string }) => {
      if (data.user_id !== userId) {
        setOtherUserTyping(true);
      }
    });

    socket.on('typing_stopped', (data: { user_id: string }) => {
      if (data.user_id !== userId) {
        setOtherUserTyping(false);
      }
    });

    socket.on('user_joined', (data: any) => {
      console.log('User joined:', data);
    });

    socket.on('user_left', (data: any) => {
      console.log('User left:', data);
    });

    return () => {
      socket.off('new_message');
      socket.off('typing_started');
      socket.off('typing_stopped');
      socket.off('user_joined');
      socket.off('user_left');
    };
  }, [socket, userId]);

  const fetchAdmins = async () => {
    try {
      const response = await fetch('/admins', {
        headers: {
          "Authorization": `Bearer ${localStorage.getItem('token')}`
        }
      });
      const data = await response.json();
      setAdmins(data.admins || []);
    } catch (error) {
      console.error('Error fetching admins:', error);
    }
  };

  const createChatSession = async () => {
    if (!selectedAdmin) return;

    try {
      const response = await fetch('/chat/api/sessions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          client_id: userId,
          admin_id: selectedAdmin.id,
        }),
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Chat session created:', result);
        setChatSessionId(result.session_id);
m
        console.log('Joining chat room:', result.session_id);
        socket?.emit('join_chat', {
          session_id: result.session_id,
          user_id: userId,
          user_type: 'client'
        });
        console.log('Join chat event emitted');

        fetchMessages(result.session_id);
      } else {
        console.error('Failed to create chat session:', response.status, await response.text());
      }
    } catch (error) {
      console.error('Error creating session:', error);
    }
  };

  const fetchMessages = async (sessionId: string) => {
    try {
      const response = await fetch(`/chat/api/sessions/${sessionId}/messages`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const data = await response.json();
      console.log('Fetched messages:', data);
      setMessages(data);
    } catch (error) {
      console.error('Error fetching messages:', error);
    }
  };

  const sendMessage = async () => {
    if (!newMessage.trim() || !socket) {
      return;
    }

    if (chatMode === 'ai') {
      const userMessage: Message = {
        id: `temp-${Date.now()}`,
        sender_id: userId,
        receiver_id: 'ai',
        content: newMessage,
        timestamp: new Date().toISOString(),
        is_read: true,
        message_type: 'user'
      };
      setMessages(prev => [...prev, userMessage]);

      const messageContent = newMessage;
      setNewMessage('');
      setIsAiThinking(true);

      try {
        const response = await fetch('/chat/api/ai-chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify({
            message: messageContent,
            user_id: userId
          })
        });

        const data = await response.json();

        const aiMessage: Message = {
          id: `ai-${Date.now()}`,
          sender_id: 'ai',
          receiver_id: userId,
          content: data.response || 'Sorry, I could not process your request.',
          timestamp: new Date().toISOString(),
          is_read: true,
          message_type: 'ai'
        };
        setMessages(prev => [...prev, aiMessage]);
      } catch (error) {
        console.error('Error getting AI response:', error);
        const errorMessage: Message = {
          id: `error-${Date.now()}`,
          sender_id: 'ai',
          receiver_id: userId,
          content: 'Sorry, I encountered an error. Please try again.',
          timestamp: new Date().toISOString(),
          is_read: true,
          message_type: 'ai'
        };
        setMessages(prev => [...prev, errorMessage]);
      } finally {
        setIsAiThinking(false);
      }
    } else {
      if (!selectedAdmin || !chatSessionId) {
        console.log('Cannot send message:', { 
          hasAdmin: !!selectedAdmin, 
          hasSession: !!chatSessionId 
        });
        return;
      }

      const messageData = {
        session_id: chatSessionId,
        sender_id: userId,
        content: newMessage,
        sender_type: 'client'
      };

      console.log('Sending message:', messageData);

      socket.emit('send_message', messageData);

      setNewMessage('');

      socket.emit('typing_stop', {
        session_id: chatSessionId,
        user_id: userId
      });
    }
  };

  const handleTyping = (value: string) => {
    setNewMessage(value);

    if (chatMode === 'ai' || !socket || !chatSessionId) return;

    if (value.trim()) {
      socket.emit('typing_start', {
        session_id: chatSessionId,
        user_id: userId
      });
    } else {
      socket.emit('typing_stop', {
        session_id: chatSessionId,
        user_id: userId
      });
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      sendMessage();
    }
  };


  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const getMessageTypeColor = (type: string) => {
    switch (type) {
      case 'auto': return 'bg-blue-100';
      case 'ai': return 'bg-green-100';
      case 'notification': return 'bg-red-100';
      default: return '';
    }
  };

  const getMessageTypeLabel = (type: string) => {
    switch (type) {
      case 'auto': return '🤖 Auto Reply';
      case 'ai': return '🧠 AI Assistant';
      case 'notification': return '⚠️ System Alert';
      default: return '';
    }
  };

  if (isMinimized) {
    return (
      <div className="fixed bottom-4 right-4 z-50">
        <Button
          onClick={() => setIsMinimized(false)}
          className="bg-blue-600 hover:bg-blue-700"
        >
          💬 Chat {chatMode === 'ai' ? '🤖' : '👨‍💼'} ({messages.length})
        </Button>
      </div>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 z-50 w-96 h-[500px] bg-white border border-gray-300 rounded-lg shadow-lg">
      <Card className="h-full flex flex-col">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">
            {chatMode === 'ai' ? '🤖 AI Assistant' : '👨‍💼 Admin Support'} - {userName}
          </CardTitle>
          <div className="flex space-x-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsMinimized(true)}
              className="h-6 w-6 p-0"
            >
              −
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="h-6 w-6 p-0"
            >
              ×
            </Button>
          </div>
        </CardHeader>

        <CardContent className="flex-1 flex flex-col p-4">
          {/* Chat Mode Toggle */}
          <div className="flex space-x-2 mb-3">
            <Button
              variant={chatMode === 'admin' ? 'default' : 'outline'}
              size="sm"
              className="flex-1"
              onClick={() => {
                setChatMode('admin');
                setMessages([]);
                setSelectedAdmin(null);
                setChatSessionId('');
              }}
            >
              👨‍💼 Admin
            </Button>
            <Button
              variant={chatMode === 'ai' ? 'default' : 'outline'}
              size="sm"
              className="flex-1"
              onClick={() => {
                setChatMode('ai');
                setMessages([]);
                setSelectedAdmin(null);
                setChatSessionId('');
              }}
            >
              🤖 AI Assistant
            </Button>
          </div>

          {chatMode === 'admin' && !selectedAdmin ? (
            <div className="flex-1">
              <h3 className="text-sm font-medium mb-2">Select an Administrator</h3>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {admins.map((admin) => (
                  <div
                    key={admin.id}
                    className="flex items-center justify-between p-2 border rounded cursor-pointer hover:bg-gray-50"
                    onClick={() => setSelectedAdmin(admin)}
                  >
                    <div>
                      <div className="text-sm font-medium">{admin.name}</div>
                      <div className="text-xs text-gray-500">@{admin.username}</div>
                    </div>
                    <Badge variant={admin.is_online ? "default" : "secondary"}>
                      {admin.is_online ? "Online" : "Offline"}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          ) : (chatMode === 'ai' || selectedAdmin) ? (
            <>
              {chatMode === 'admin' && selectedAdmin && (
                <div className="flex items-center justify-between mb-2">
                  <div className="text-sm">
                    Chatting with <strong>{selectedAdmin.name}</strong>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setSelectedAdmin(null);
                      setMessages([]);
                      setChatSessionId('');
                    }}
                  >
                    Change Admin
                  </Button>
                </div>
              )}

              {chatMode === 'ai' && (
                <div className="text-xs text-gray-600 mb-2 p-2 bg-blue-50 rounded">
                  💡 Ask me about energy consumption, devices, billing, or any system features!
                </div>
              )}

              <div className="flex-1 overflow-y-auto border rounded p-2 mb-2 max-h-64">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`mb-2 p-2 rounded text-sm ${
                      message.sender_id === userId
                        ? 'bg-blue-100 ml-8'
                        : getMessageTypeColor(message.message_type) || 'bg-gray-100 mr-8'
                    }`}
                  >
                    {message.message_type !== 'user' && (
                      <div className="text-xs font-medium mb-1 text-gray-600">
                        {getMessageTypeLabel(message.message_type)}
                      </div>
                    )}
                    <div className="font-medium text-xs mb-1">
                      {message.sender_id === userId ? 'You' :
                       message.message_type === 'auto' ? 'Auto Reply' :
                       message.message_type === 'ai' ? 'AI Assistant' :
                       message.message_type === 'notification' ? 'System' :
                       selectedAdmin?.name || 'Admin'}
                    </div>
                    <div>{message.content}</div>
                    <div className="text-xs text-gray-500 mt-1">
                      {new Date(message.timestamp).toLocaleTimeString()}
                      {message.is_read && message.sender_id === userId && (
                        <span className="ml-1">✓</span>
                      )}
                    </div>
                  </div>
                ))}
                {otherUserTyping && chatMode === 'admin' && (
                  <div className="text-xs text-gray-500 italic">
                    {selectedAdmin?.name} is typing...
                  </div>
                )}
                {isAiThinking && chatMode === 'ai' && (
                  <div className="text-xs text-gray-500 italic">
                    AI is thinking...
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              <div className="flex space-x-2">
                <Input
                  value={newMessage}
                  onChange={(e) => handleTyping(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder={chatMode === 'ai' ? 'Ask me anything...' : 'Type your message...'}
                  className="flex-1"
                  disabled={isAiThinking}
                />
                <Button onClick={sendMessage} disabled={!newMessage.trim() || isAiThinking}>
                  Send
                </Button>
              </div>
            </>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
};