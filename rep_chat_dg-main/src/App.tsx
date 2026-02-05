import React, { useState, useEffect } from 'react';
import ChatRoom from './components/ChatRoom';
import UserSelector from './components/UserSelector';

interface User {
  id: number;
  username: string;
  email: string;
}

function App() {
  const [users, setUsers] = useState<User[]>([]);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [otherUser, setOtherUser] = useState<User | null>(null);
  const [chatRoomId, setChatRoomId] = useState<string | null>(null);

  useEffect(() => {
    // Charger les utilisateurs depuis l'API
    fetch('http://localhost:3001/api/users')
      .then(res => res.json())
      .then(data => {
        setUsers(data);
        // Simuler la connexion avec le premier utilisateur
        setCurrentUser(data[0]);
      })
      .catch(err => console.error('Erreur lors du chargement des utilisateurs:', err));
  }, []);

  const handleStartChat = async (selectedUser: User) => {
    if (!currentUser) return;

    try {
      // Créer ou rejoindre une room de chat
      const response = await fetch('http://localhost:3001/api/chat/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user1Id: currentUser.id,
          user2Id: selectedUser.id,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setChatRoomId(data.roomId);
        setOtherUser(selectedUser);
      }
    } catch (error) {
      console.error('Erreur lors de la création du chat:', error);
    }
  };

  const handleReport = async (reason: string) => {
    if (!chatRoomId || !currentUser) return;

    try {
      await fetch(`http://localhost:3001/api/chat/${chatRoomId}/report`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          reason,
          reportedBy: currentUser.id,
        }),
      });
    } catch (error) {
      console.error('Erreur lors du signalement:', error);
    }
  };

  const handleBackToUsers = () => {
    setChatRoomId(null);
    setOtherUser(null);
  };

  if (!currentUser) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto mb-4"></div>
          <p className="text-gray-600">Chargement...</p>
        </div>
      </div>
    );
  }

  if (chatRoomId && otherUser) {
    return (
      <div className="relative">
        <button
          onClick={handleBackToUsers}
          className="absolute top-4 left-4 z-10 px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
        >
          ← Retour
        </button>
        <ChatRoom
          roomId={chatRoomId}
          currentUser={currentUser}
          otherUser={otherUser}
          onReport={handleReport}
        />
      </div>
    );
  }

  return (
    <UserSelector
      users={users}
      currentUser={currentUser}
      onStartChat={handleStartChat}
    />
  );
}

export default App;