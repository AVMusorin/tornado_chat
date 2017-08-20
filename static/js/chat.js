
$(document).ready(function() {
        var $chatbox = $('.chatbox'),
            $chatboxTitle = $('.chatbox__title'),
            $chatboxTitleClose = $('.chatbox__title__close'),
            $chatboxCredentials = $('.chatbox__credentials');
            $chatboxWS = $("#start-ws");
        $chatboxTitle.on('click', function() {
            $chatbox.toggleClass('chatbox--tray');
        });
        $chatboxTitleClose.on('click', function(e) {
            e.stopPropagation();
            $chatbox.addClass('chatbox--closed');
            if (window.sock) {
                window.sock.close();
            }
        });
        $chatbox.on('transitionend', function() {
            if ($chatbox.hasClass('chatbox--closed')) $chatbox.remove();
        });
        $chatboxCredentials.on('submit', function(e) {
            e.preventDefault();
            $chatbox.removeClass('chatbox--empty');
        });

        $chatboxWS.on('click', function(e){
            if (!("WebSocket" in window)) {
                alert("Ваш браузер не поддерживает web sockets");
            }
            else {
                if ($("#inputName").val() && $("#inputEmail").val()) {
                    alert("Начало соединения");
                    setup();
                }
            }
        });
})

function setup(){
    var host = "ws://127.0.0.1:8080/ws";
    var socket = new WebSocket(host); 
    window.sock = socket;  
    var $txt = $("#message");
    var $btnSend = $("#sendmessage");
    var inputName = $("#inputName").val();
    var inputEmail = $("#inputEmail").val();
    $.cookie('name', inputName);
    $.cookie('email', inputEmail);

    $txt.focus();
    $btnSend.on('click',function(){
        var text = $txt.val();
        if(text == ""){
            return;
        }
        socket.send(text);
        clientRequest(text);
        $txt.val(""); 
        });

        $txt.keypress(function(evt){
            if(evt.which == 13){
                $btnSend.click();
            }
        });

        if(socket){
            socket.onopen = function(){
                managerResponse("Я мастер компании The Sarai, чем я могу Вам помочь?");
                socket.send(inputName + "|" + inputEmail);
            }
            socket.onmessage = function(msg){
                if (msg.data.indexOf('CLIENT') + 1) {
                    clientRequest(msg.data.substr(6, msg.data.length));
                }
                else {
                managerResponse(msg.data);
            }
            }
            socket.onclose = function(){
                showServerResponse("The connection has been closed.");
                window.sock = false;
            }
        }else{
            console.log("invalid socket");
        } 
    }; 

function showServerResponse(txt){
    var p = document.createElement('p');
    p.innerHTML = txt;
    document.getElementById('messages__box').appendChild(p); 
}

function clientRequest(txt) {
    $("#messages__box").append("<div class='chatbox__body__message chatbox__body__message--right'> <img src='https://s3.amazonaws.com/uifaces/faces/twitter/arashmil/128.jpg' alt='Picture'> <p>" + txt + "</p> </div>");
}

function managerResponse(txt) {
    $("#messages__box").append("<div class='chatbox__body__message chatbox__body__message--left'> <img src='../img/person.png' alt='Picture'> <p>" + txt + "</p> </div>");
}  