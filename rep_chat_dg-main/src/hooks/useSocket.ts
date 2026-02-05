import { useEffect, useRef, useState } from 'react';
import { io, Socket } from 'socket.io-client';

interface Message {
  id: string;
  type: 'text' | 'image';
  content: string;
  userId: number;
  username: string;
  timestamp: Date;
  roomId: string;
}

interface UseSocketReturn {
  socket: Socket | null;
  messages: Message[];
  isConnected: boolean;
  joinRoom: (roomId: string, userId: number, username: string) => void;
  sendMessage: (roomId: string, message: string, userId: number, username: string) => void;
  sendImage: (roomId: string, imageUrl: string, userId: number, username: string) => void;
  typing: (roomId: string, username: string) => void;
  stopTyping: (roomId: string) => void;
}

export const useSocket = (serverUrl = 'http://localhost:3001'): UseSocketReturn => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [userTyping, setUserTyping] = useState<string | null>(null);

  useEffect(() => {
    const newSocket = io(serverUrl);
    setSocket(newSocket);

    newSocket.on('connect', () => {
      setIsConnected(true);
      console.log('Connecté au serveur');
    });

    newSocket.on('disconnect', () => {
      setIsConnected(false);
      console.log('Déconnecté du serveur');
    });

    newSocket.on('receive_message', (message: Message) => {
      setMessages(prev => [...prev, message]);
    });

    newSocket.on('user_joined', (data: { username: string; message: string }) => {
      console.log(data.message);
    });

    newSocket.on('user_left', (data: { username: string; message: string }) => {
      console.log(data.message);
    });

    newSocket.on('user_typing', (data: { username: string }) => {
      setUserTyping(data.username);
    });

    newSocket.on('user_stop_typing', () => {
      setUserTyping(null);
    });

    return () => {
      newSocket.close();
    };
  }, [serverUrl]);

  const joinRoom = (roomId: string, userId: number, username: string) => {
    socket?.emit('join_room', { roomId, userId, username });
  };

  const sendMessage = (roomId: string, message: string, userId: number, username: string) => {
    if (socket && message.trim()) {
      socket.emit('send_message', {
        roomId,
        message,
        userId,
        username,
        timestamp: new Date()
      });
    }
  };

  const sendImage = (roomId: string, imageUrl: string, userId: number, username: string) => {
    if (socket && imageUrl) {
      socket.emit('send_image', {
        roomId,
        imageUrl,
        userId,
        username,
        timestamp: new Date()
      });
    }
  };

  const typing = (roomId: string, username: string) => {
    socket?.emit('typing', { roomId, username });
  };

  const stopTyping = (roomId: string) => {
    socket?.emit('stop_typing', { roomId });
  };

  return {
    socket,
    messages,
    isConnected,
    joinRoom,
    sendMessage,
    sendImage,
    typing,
    stopTyping
  };
};