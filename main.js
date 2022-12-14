import {createBoard, playMove} from "./connect4.js"

window.addEventListener("DOMContentLoaded", () => {
    const board = document.querySelector(".board");
    const form = document.getElementById("chat-form");
    
    createBoard(board);

    const websocket = new WebSocket(getWebSocketServer());
    // sendMessage(form, websocket);
    initGame(websocket);
    recieveMoves(board, websocket);
    sendMoves(board, websocket);
});

function showMessage(message){
    window.setTimeout(() => window.alert(message), 50);
}


function sendMoves(board, websocket){
 // prevent moves from being sent to spectators
    const params = new URLSearchParams(window.location.search);
    if (params.has("watch")){
        return;
    }

    // send play event for moves in a column when clicking the column 
    board.addEventListener("click", ({target}) => {
       const column = target.dataset.column;
        
       // ignore clicks outside the board
       if(column === undefined){
           return;
       }
       const event = {
           type: "play",
           column: parseInt(column, 10),
       };
       websocket.send(JSON.stringify(event));
    })
}

function recieveMoves(board, websocket){
    websocket.addEventListener("message", ({data}) => {
        const event = JSON.parse(data);
        switch (event.type){
            case "init":
                document.querySelector(".join").href = "?join=" + event.join;
                document.querySelector(".watch").href = "?watch=" + event.watch;
            case "play":
                playMove(board, event.player, event.column, event.row);
                break;
            case "win":
                showMessage(`Player ${event.player} wins!`);
                websocket.close(1000);
                break; 
            case "chat":
                displayMessages(event.message);
                break;
            case "error":
                showMessage(event.message);
                break; 
            default:
                throw new Error (`Unsupported event type ${event.type}.`);
        }
    });
}

function initGame(websocket){
    websocket.addEventListener("open" ,() => {
        const params = new URLSearchParams(window.location.search)
        let event = {type : "init"};
        if (params.has("join")){
            event.join = params.get("join")
        }else if (params.has("watch")) {
            event.watch = params.get("watch")
        }else {
        }
        websocket.send(JSON.stringify(event));
    });
}

function getWebSocketServer(){
   if(window.location.host == "asiakn.github.io"){
       return "wss://connect4-game.herokuapp.com/";
   } else if(window.location.host == "localhost:8000"){
       return "ws://localhost:8001";
   }else{
       throw new Error(`Unsupported host: ${window.location.host}`);
   }
}

function sendMessage (form, websocket){
    form.addEventListener("submit", (form) => {
        const chatInput = document.getElementById('chat-input');
        const event = {
            type: "chat",
            message: chatInput.value
        };
        websocket.send(JSON.stringify(event));
        chatInput.value = '';
        form.preventDefault();
    })
}

function displayMessages(message) {

    const messages = document.getElementById("chatbox")
    const linebreak = document.createElement('br');

    const content = document.createTextNode(message)
    messages.appendChild(linebreak);
    messages.appendChild(content)
}