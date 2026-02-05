import React, { useState, useRef, useEffect } from 'react';
import { Send, Image, AlertTriangle } from 'lucide-react';
import { useSocket } from '../hooks/useSocket';

interface User {
  id: number;
  username: string;
  email: string;
}

interface ChatRoomProps {
  roomId: string;
  currentUser: User;
  otherUser: User;
  onReport: (reason: string) => void;
}

interface Message {
  id: string;
  type: 'text' | 'image';
  content: string;
  userId: number;
  username: string;
  timestamp: Date;
  roomId: string;
}

const ChatRoom: React.FC<ChatRoomProps> = ({ roomId, currentUser, otherUser, onReport }) => {
  const [message, setMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [showReportModal, setShowReportModal] = useState(false);
  const [reportReason, setReportReason] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const { messages, isConnected, joinRoom, sendMessage, sendImage, typing, stopTyping } = useSocket();

  useEffect(() => {
    if (isConnected) {
      joinRoom(roomId, currentUser.id, currentUser.username);
    }
  }, [isConnected, roomId, currentUser]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = () => {
    if (message.trim()) {
      sendMessage(roomId, message, currentUser.id, currentUser.username);
      setMessage('');
      handleStopTyping();
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    } else {
      handleTyping();
    }
  };

  const handleTyping = () => {
    if (!isTyping) {
      setIsTyping(true);
      typing(roomId, currentUser.username);
    }

    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }

    typingTimeoutRef.current = setTimeout(() => {
      handleStopTyping();
    }, 1000);
  };

  const handleStopTyping = () => {
    setIsTyping(false);
    stopTyping(roomId);
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }
  };

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('image', file);

    try {
      const response = await fetch('http://localhost:3001/upload', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        sendImage(roomId, data.imageUrl, currentUser.id, currentUser.username);
      } else {
        alert('Erreur lors de l\'upload de l\'image');
      }
    } catch (error) {
      console.error('Erreur:', error);
      alert('Erreur lors de l\'upload de l\'image');
    }

    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleReport = () => {
    if (reportReason.trim()) {
      onReport(reportReason);
      setShowReportModal(false);
      setReportReason('');
      alert('Signalement envoyé avec succès');
    }
  };

  const formatTimestamp = (timestamp: Date) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('fr-FR', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div className="flex flex-col h-screen bg-white">
      {/* En-tête */}
      <div className="bg-white border-b border-gray-200 p-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gray-300 rounded-full flex items-center justify-center">
            <span className="text-gray-600 font-medium">
              {otherUser.username.charAt(0).toUpperCase()}
            </span>
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-900">{otherUser.username}</h2>
            <p className="text-sm text-gray-500">
              {isConnected ? 'En ligne' : 'Hors ligne'}
            </p>
          </div>
        </div>
        
        <button
          onClick={() => setShowReportModal(true)}
          className="p-2 text-gray-500 hover:text-red-500 hover:bg-red-50 rounded-full transition-colors"
          title="Signaler cette conversation"
        >
          <AlertTriangle size={20} />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg: Message) => (
          <div
            key={msg.id}
            className={`flex ${msg.userId === currentUser.id ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                msg.userId === currentUser.id
                  ? 'bg-gray-900 text-white'
                  : 'bg-gray-100 text-gray-900'
              }`}
            >
              {msg.type === 'text' ? (
                <p className="break-words">{msg.content}</p>
              ) : (
                <img
                  src={`http://localhost:3001${msg.content}`}
                  alt="Image partagée"
                  className="max-w-full h-auto rounded"
                />
              )}
              <p className={`text-xs mt-1 ${
                msg.userId === currentUser.id ? 'text-gray-300' : 'text-gray-500'
              }`}>
                {formatTimestamp(msg.timestamp)}
              </p>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Barre de saisie */}
      <div className="bg-white border-t border-gray-200 p-4">
        <div className="flex items-center space-x-3">
          <button
            onClick={() => fileInputRef.current?.click()}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-full transition-colors"
            title="Envoyer une image"
          >
            <Image size={20} />
          </button>
          
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleImageUpload}
            className="hidden"
          />
          
          <div className="flex-1 relative">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Tapez votre message..."
              className="w-full px-4 py-2 border border-gray-300 rounded-full focus:outline-none focus:border-gray-500"
            />
          </div>
          
          <button
            onClick={handleSendMessage}
            disabled={!message.trim()}
            className="p-2 bg-gray-900 text-white rounded-full hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send size={20} />
          </button>
        </div>
      </div>

      {/* Modal de signalement */}
      {showReportModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4 text-gray-900">
              Signaler cette conversation
            </h3>
            <textarea
              value={reportReason}
              onChange={(e) => setReportReason(e.target.value)}
              placeholder="Expliquez la raison du signalement..."
              className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:border-gray-500 mb-4"
              rows={4}
            />
            <div className="flex space-x-3">
              <button
                onClick={() => setShowReportModal(false)}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Annuler
              </button>
              <button
                onClick={handleReport}
                disabled={!reportReason.trim()}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Signaler
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatRoom;