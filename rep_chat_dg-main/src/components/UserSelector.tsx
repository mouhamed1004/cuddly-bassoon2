import React from 'react';
import { MessageCircle } from 'lucide-react';

interface User {
  id: number;
  username: string;
  email: string;
}

interface UserSelectorProps {
  users: User[];
  currentUser: User;
  onStartChat: (otherUser: User) => void;
}

const UserSelector: React.FC<UserSelectorProps> = ({ users, currentUser, onStartChat }) => {
  const otherUsers = users.filter(user => user.id !== currentUser.id);

  return (
    <div className="min-h-screen bg-white flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <MessageCircle size={48} className="mx-auto text-gray-900 mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Chat en temps réel
          </h1>
          <p className="text-gray-600">
            Connecté en tant que <strong>{currentUser.username}</strong>
          </p>
        </div>

        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Démarrer une conversation avec :
          </h2>
          
          {otherUsers.map((user) => (
            <button
              key={user.id}
              onClick={() => onStartChat(user)}
              className="w-full p-4 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-gray-300 transition-colors text-left"
            >
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gray-300 rounded-full flex items-center justify-center">
                  <span className="text-gray-600 font-medium">
                    {user.username.charAt(0).toUpperCase()}
                  </span>
                </div>
                <div>
                  <p className="font-medium text-gray-900">{user.username}</p>
                  <p className="text-sm text-gray-500">{user.email}</p>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default UserSelector;