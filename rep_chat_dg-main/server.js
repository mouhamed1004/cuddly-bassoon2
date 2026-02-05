import express from 'express';
import { createServer } from 'http';
import { Server as SocketIOServer } from 'socket.io';
import multer from 'multer';
import path from 'path';
import fs from 'fs';
import { v4 as uuidv4 } from 'uuid';
import cors from 'cors';

const app = express();
const server = createServer(app);
const io = new SocketIOServer(server, {
  cors: {
    origin: "http://localhost:5173",
    methods: ["GET", "POST"],
    credentials: true
  }
});

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('public'));
app.use('/uploads', express.static('uploads'));

// Créer le dossier uploads s'il n'existe pas
if (!fs.existsSync('uploads')) {
  fs.mkdirSync('uploads');
}

// Configuration multer pour l'upload d'images
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, 'uploads/');
  },
  filename: (req, file, cb) => {
    const uniqueName = `${Date.now()}-${uuidv4()}${path.extname(file.originalname)}`;
    cb(null, uniqueName);
  }
});

const upload = multer({
  storage: storage,
  limits: {
    fileSize: 5 * 1024 * 1024 // 5MB max
  },
  fileFilter: (req, file, cb) => {
    const allowedTypes = /jpeg|jpg|png|gif|webp/;
    const extname = allowedTypes.test(path.extname(file.originalname).toLowerCase());
    const mimetype = allowedTypes.test(file.mimetype);
    
    if (extname && mimetype) {
      return cb(null, true);
    } else {
      cb(new Error('Seules les images sont autorisées'));
    }
  }
});

// Base de données en mémoire (à remplacer par une vraie DB en production)
let chatRooms = {};
let messages = {};
let users = {};

// Route pour upload d'image
app.post('/upload', upload.single('image'), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'Aucune image uploadée' });
  }
  
  const imageUrl = `/uploads/${req.file.filename}`;
  res.json({ imageUrl });
});

// Simuler des utilisateurs (en production, utilisez votre système d'authentification)
const mockUsers = [
  { id: 1, username: 'Alice', email: 'alice@example.com' },
  { id: 2, username: 'Bob', email: 'bob@example.com' }
];

app.get('/api/users', (req, res) => {
  res.json(mockUsers);
});

// Route pour créer/rejoindre une room de chat
app.post('/api/chat/create', (req, res) => {
  const { user1Id, user2Id } = req.body;
  
  // Créer un ID unique pour la room basé sur les IDs des utilisateurs
  const roomId = [user1Id, user2Id].sort().join('-');
  
  if (!chatRooms[roomId]) {
    chatRooms[roomId] = {
      id: roomId,
      participants: [user1Id, user2Id],
      createdAt: new Date(),
      isReported: false
    };
    messages[roomId] = [];
  }
  
  res.json({ roomId, room: chatRooms[roomId] });
});

// Route pour récupérer l'historique des messages
app.get('/api/chat/:roomId/messages', (req, res) => {
  const { roomId } = req.params;
  const roomMessages = messages[roomId] || [];
  res.json(roomMessages);
});

// Route pour signaler une conversation (pour modération)
app.post('/api/chat/:roomId/report', (req, res) => {
  const { roomId } = req.params;
  const { reason, reportedBy } = req.body;
  
  if (chatRooms[roomId]) {
    chatRooms[roomId].isReported = true;
    chatRooms[roomId].reportReason = reason;
    chatRooms[roomId].reportedBy = reportedBy;
    chatRooms[roomId].reportedAt = new Date();
    
    // En production, vous pourriez notifier les modérateurs
    console.log(`Chat room ${roomId} signalée par l'utilisateur ${reportedBy}: ${reason}`);
    
    res.json({ success: true, message: 'Conversation signalée avec succès' });
  } else {
    res.status(404).json({ error: 'Conversation non trouvée' });
  }
});

// Route pour les modérateurs - récupérer les conversations signalées
app.get('/api/admin/reported-chats', (req, res) => {
  const reportedChats = Object.values(chatRooms)
    .filter(room => room.isReported)
    .map(room => ({
      ...room,
      messages: messages[room.id] || []
    }));
  
  res.json(reportedChats);
});

// Gestion des connexions Socket.IO
io.on('connection', (socket) => {
  console.log('Utilisateur connecté:', socket.id);

  // L'utilisateur rejoint une room de chat
  socket.on('join_room', (data) => {
    const { roomId, userId, username } = data;
    socket.join(roomId);
    users[socket.id] = { userId, username, roomId };
    
    // Notifier les autres utilisateurs de la room
    socket.to(roomId).emit('user_joined', {
      userId,
      username,
      message: `${username} a rejoint le chat`
    });
    
    console.log(`${username} a rejoint la room ${roomId}`);
  });

  // Réception d'un message texte
  socket.on('send_message', (data) => {
    const { roomId, message, userId, username, timestamp } = data;
    
    const messageData = {
      id: uuidv4(),
      type: 'text',
      content: message,
      userId,
      username,
      timestamp: timestamp || new Date(),
      roomId
    };
    
    // Sauvegarder le message
    if (!messages[roomId]) {
      messages[roomId] = [];
    }
    messages[roomId].push(messageData);
    
    // Envoyer le message à tous les utilisateurs de la room
    io.to(roomId).emit('receive_message', messageData);
    
    console.log(`Message de ${username} dans room ${roomId}: ${message}`);
  });

  // Réception d'un message image
  socket.on('send_image', (data) => {
    const { roomId, imageUrl, userId, username, timestamp } = data;
    
    const messageData = {
      id: uuidv4(),
      type: 'image',
      content: imageUrl,
      userId,
      username,
      timestamp: timestamp || new Date(),
      roomId
    };
    
    // Sauvegarder le message
    if (!messages[roomId]) {
      messages[roomId] = [];
    }
    messages[roomId].push(messageData);
    
    // Envoyer l'image à tous les utilisateurs de la room
    io.to(roomId).emit('receive_message', messageData);
    
    console.log(`Image de ${username} dans room ${roomId}: ${imageUrl}`);
  });

  // Indicateur de saisie
  socket.on('typing', (data) => {
    const { roomId, username } = data;
    socket.to(roomId).emit('user_typing', { username });
  });

  socket.on('stop_typing', (data) => {
    const { roomId } = data;
    socket.to(roomId).emit('user_stop_typing');
  });

  // Déconnexion
  socket.on('disconnect', () => {
    const user = users[socket.id];
    if (user) {
      socket.to(user.roomId).emit('user_left', {
        userId: user.userId,
        username: user.username,
        message: `${user.username} a quitté le chat`
      });
      delete users[socket.id];
    }
    console.log('Utilisateur déconnecté:', socket.id);
  });
});

const PORT = process.env.PORT || 3001;
server.listen(PORT, () => {
  console.log(`Serveur de chat en cours d'exécution sur le port ${PORT}`);
});