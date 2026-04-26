const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const app = express();
const server = http.createServer(app);
const io = new Server(server);

app.use(express.json());
app.use(express.static('public'));

let machines = {};
let autorisations = {};

io.on('connection', (socket) => {
  console.log('Nouvelle connexion : ' + socket.id);

  socket.on('enregistrer', (data) => {
    machines[data.id] = {
      socketId: socket.id,
      nom: data.nom,
      autorise: autorisations[data.id] || false
    };
    console.log('Machine enregistrée : ' + data.nom);
    io.emit('liste_machines', machines);
  });

  socket.on('demande_autorisation', (data) => {
    const machine = machines[data.id];
    if (machine) {
      io.to(machine.socketId).emit('demande_autorisation');
    }
  });

  socket.on('reponse_autorisation', (data) => {
    if (data.accepte) {
      autorisations[data.id] = true;
      if (machines[data.id]) {
        machines[data.id].autorise = true;
      }
    }
    io.emit('resultat_autorisation', data);
  });

  socket.on('screenshot', (data) => {
    io.emit('screenshot_' + data.id, data.image);
  });

  socket.on('commande', (data) => {
    const machine = machines[data.id];
    if (machine && machines[data.id].autorise) {
      io.to(machine.socketId).emit('commande', data);
    }
  });

  socket.on('disconnect', () => {
    for (let id in machines) {
      if (machines[id].socketId === socket.id) {
        console.log('Machine déconnectée : ' + machines[id].nom);
        delete machines[id];
        io.emit('liste_machines', machines);
      }
    }
  });
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log('Serveur démarré sur le port ' + PORT);
});