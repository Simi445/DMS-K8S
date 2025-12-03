import React, { useState, useEffect, useRef } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import io, { Socket } from 'socket.io-client';

interface ChatSession {
  id: string;
  client_id: string;
  admin_id: string;
  created_at: string;
  last_activity: string;
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

interface AdminChatProps {
  adminId: string;
  adminName: string;
}

export const AdminChat: React.FC<AdminChatProps> = ({ adminId, adminName }) => {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [selectedSession, setSelectedSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [socket, setSocket] = useState<Socket | null>(null);
  const [clientTyping, setClientTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const socketConnection = io('/', {
      path: '/socket.io',
      transports: ['polling']
    });

    setSocket(socketConnection);

    return () => {
      socketConnection.disconnect();
    };
  }, []);

  useEffect(() => {
    fetchActiveSessions();
    const interval = setInterval(fetchActiveSessions, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (selectedSession && socket) {
      socket.emit('join_chat', {
        session_id: selectedSession.id,
        user_id: adminId,
        user_type: 'admin'
      });

      fetchMessages(selectedSession.id);
    }
  }, [selectedSession, socket]);

  useEffect(() => {
    if (!socket) return;

    socket.on('new_message', (message: Message) => {
      setMessages(prev => [...prev, message]);
      fetchActiveSessions();
    });

    socket.on('typing_started', (data: { user_id: string }) => {
      if (data.user_id !== adminId) {
        setClientTyping(true);
      }
    });

    socket.on('typing_stopped', (data: { user_id: string }) => {
      if (data.user_id !== adminId) {
        setClientTyping(false);
      }
    });

    return () => {
      socket.off('new_message');
      socket.off('typing_started');
      socket.off('typing_stopped');
    };
  }, [socket, adminId]);

  const fetchActiveSessions = async () => {
    try {
      const response = await fetch('/chat/api/sessions/active', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const data = await response.json();
      setSessions(data);
    } catch (error) {
      console.error('Error fetching sessions:', error);
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
      setMessages(data);
    } catch (error) {
      console.error('Error fetching messages:', error);
    }
  };

  const sendMessage = () => {
    if (!newMessage.trim() || !selectedSession || !socket) return;

    const messageData = {
      session_id: selectedSession.id,
      sender_id: adminId,
      content: newMessage,
      sender_type: 'admin'
    };

    socket.emit('send_message', messageData);
    socket.emit('typing_stop', {
      session_id: selectedSession.id,
      user_id: adminId
    });
    setNewMessage('');
  };

  const handleTyping = (value: string) => {
    setNewMessage(value);
    
    if (!socket || !selectedSession) return;

    if (value.trim()) {
      socket.emit('typing_start', {
        session_id: selectedSession.id,
        user_id: adminId
      });
    } else {
      socket.emit('typing_stop', {
        session_id: selectedSession.id,
        user_id: adminId
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

  return (
    <div className="grid grid-cols-12 gap-4 h-[600px]">
      {/* Sessions List */}
      <div className="col-span-4">
        <Card className="h-full">
          <CardHeader>
            <CardTitle className="text-lg">Active Chat Sessions</CardTitle>
          </CardHeader>
          <CardContent className="overflow-y-auto max-h-[520px]">
            {sessions.length === 0 ? (
              <p className="text-gray-500 text-sm">No active sessions</p>
            ) : (
              <div className="space-y-2">
                {sessions.map((session) => (
                  <div
                    key={session.id}
                    onClick={() => setSelectedSession(session)}
                    className={`p-3 border rounded cursor-pointer hover:bg-gray-50 ${
                      selectedSession?.id === session.id ? 'bg-blue-50 border-blue-300' : ''
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-medium text-sm">User: {session.client_id}</p>
                        <p className="text-xs text-gray-500">
                          {new Date(session.last_activity).toLocaleTimeString()}
                        </p>
                      </div>
                      <Badge variant="outline" className="text-xs">Active</Badge>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Chat Window */}
      <div className="col-span-8">
        {selectedSession ? (
          <Card className="h-full flex flex-col">
            <CardHeader>
              <CardTitle className="text-lg">
                Chat with User {selectedSession.client_id}
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col">
              {/* Messages */}
              <div className="flex-1 overflow-y-auto mb-4 space-y-3 max-h-[440px]">
                {messages.map((msg) => {
                  const isAdmin = msg.sender_id === adminId;
                  return (
                    <div
                      key={msg.id}
                      className={`flex ${isAdmin ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-[70%] p-3 rounded-lg ${
                          isAdmin
                            ? 'bg-blue-500 text-white'
                            : msg.message_type === 'auto'
                            ? 'bg-green-100'
                            : msg.message_type === 'ai'
                            ? 'bg-purple-100'
                            : 'bg-gray-100'
                        }`}
                      >
                        {msg.message_type !== 'user' && (
                          <div className="text-xs mb-1 font-semibold">
                            {msg.message_type === 'auto' && '🤖 Auto Reply'}
                            {msg.message_type === 'ai' && '🧠 AI Assistant'}
                          </div>
                        )}
                        <p className="text-sm">{msg.content}</p>
                        <p className={`text-xs mt-1 ${isAdmin ? 'text-blue-100' : 'text-gray-500'}`}>
                          {new Date(msg.timestamp).toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                  );
                })}
                {clientTyping && (
                  <div className="flex justify-start">
                    <div className="bg-gray-100 p-3 rounded-lg">
                      <p className="text-xs text-gray-500 italic">Client is typing...</p>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Input */}
              <div className="flex space-x-2">
                <Input
                  value={newMessage}
                  onChange={(e) => handleTyping(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Type your message..."
                  className="flex-1"
                />
                <Button onClick={sendMessage}>Send</Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          <Card className="h-full flex items-center justify-center">
            <p className="text-gray-500">Select a session to view messages</p>
          </Card>
        )}
      </div>
    </div>
  );
};
