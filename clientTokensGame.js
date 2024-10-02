function escapeHtml(unsafe) {
  return unsafe
   .replace(/&/g, "&amp;")
   .replace(/</g, "&lt;")
   .replace(/>/g, "&gt;")
   .replace(/"/g, "&quot;")
   .replace(/'/g, "&#039;");
 }

 function getWebSocketServer() {
  if (window.location.host === "localhost") {
    return "ws://localhost:8765";
  } else {
    return "wss://token-game-aa782c60035f.herokuapp.com";
  }
}

const socket = new WebSocket(getWebSocketServer());

socket.onopen = (event) => {
  console.log('WebSocket connection opened');
};

socket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Handle the received data
  console.log('Data:', data);
  if ('h' in data) { // history
    document.getElementById('existingText').innerHTML = escapeHtml(data.h);
  }

  if ('u' in data) { // user count
    document.getElementById('onlineUsers').innerHTML = data.u; // integer
  }

  if ('s' in data) { // new token
    document.getElementById('existingText').innerHTML += (' ' + escapeHtml(data.s));
    const uw = document.getElementById('userWord')
    uw.innerHTML = '';
    uw.contentEditable = true;
    uw.style.backgroundColor = '#FFFFFF';
    uw.focus();
  }
};

window.onload = function() {
  const uw = document.getElementById('userWord')
  uw.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' || event.key === ' ') {
      socket.send(JSON.stringify({'s':uw.innerText}));
      uw.contentEditable = false;
      uw.style.backgroundColor = '#DDDD99';
      event.preventDefault();
    }
  });

  document.getElementById('gameText').addEventListener('click', (event) => {
    uw.focus();
  });
}