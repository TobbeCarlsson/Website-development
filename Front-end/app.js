'use strict';


var date = new Date();
var hash = "";
var index = 0;
var scrollerId;
var ratingIndex = 1;
var finishedDialogue;

window.onload = function(){
    this.scrollTop = 0;
    // Change to correct URL, probably "https://www.agnes.tv/new_dialogue"
    fetch("http://127.0.0.1:5000/new_dialogue", 
{
    headers: {
        'Content-type': 'application/json',
        'Accept': 'application/json'
    },
    }).then(res=>{

        if(res.ok){
            return res.json()
        }else{
            alert("something is wrong")
        }
    }).then(jsonResponse=>{
        console.log(jsonResponse);
        hash = jsonResponse.hash;
        addVideoAndSound();
        hideForm();
        update(jsonResponse);
} 
).catch((err) => console.error(err)); 
}

function addVideoAndSound(){
   var elem = document.createElement('img');
   elem.setAttribute('id','video');
   elem.setAttribute('src','http://127.0.0.1:5000/video_feed/'+hash);
   document.getElementById('videowrapper').appendChild(elem);

   var audioelem = document.createElement('source');
   audioelem.setAttribute('src','http://127.0.0.1:5000/audio_feed/'+hash);
   audioelem.setAttribute('type','audio/wav');
   document.getElementById('audio').appendChild(audioelem);
}
 
function update(dialogue){
    const optionsgroup = document.getElementById("options-group");
    optionsgroup.innerHTML = '';

    let history = Object.values(dialogue.history[index]);
    let options = history[4];
    let line = history[3];
    index++;
    
    // add robot line to chatbox
    var elem = document.createElement('div');
    elem.textContent += line;
    elem.setAttribute('id','reply');
    document.getElementById('chatbox').appendChild(elem);
    var chatbox = document.getElementById('chatbox');
    chatbox.scrollTop = chatbox.scrollHeight;
    // add to rating chat log
    var postelem = document.createElement('div');
    postelem.textContent += line;
    postelem.setAttribute('id','reply');
    document.getElementById('postchatbox').appendChild(postelem);
    var postchatbox = document.getElementById('postchatbox');
    postchatbox.scrollTop = postchatbox.scrollHeight;
    
    for (var i = 0; i < options.length; i++) {
            createButton(i+1,options[i]);
        }
}

function evaluate(dialogue){
    finishedDialogue = dialogue;
    let history = Object.values(dialogue.history);
    const line = history[0]["line"];
    var elem = document.createElement('div');
    elem.textContent += line;
    elem.setAttribute('id','ratingmsg');
    document.getElementById('ratingchatbox').appendChild(elem);
    // document.getElementById("body").style.overflow = "visible";
    scrollerId = startScroll();
}

function createButton(number, line){
    let btn = document.createElement("button");
    btn.innerHTML = line;
    let functioncall = "optionPress("+number.toString()+")";
    btn.setAttribute('onclick',functioncall);
    if(number == 1){
        btn.setAttribute('id','firstbtn');
    }if(number == 2){
        btn.setAttribute('id','secondbtn');
    }if(number == 3){
        btn.setAttribute('id','thirdbtn');
    }if(number == 4){
        btn.setAttribute('id','fourthbtn');
    }if(number == 5){
        btn.setAttribute('id','fifthbtn');
    }if(number == 6){
        btn.setAttribute('id','sixthbtn');
    }if(number == 7){
        btn.setAttribute('id','seventhbtn');
    }if(number == 8){
        btn.setAttribute('id','eightbtn');
    }if(number == 9){
        btn.setAttribute('id','ninthbtn');
    }if(number == 10){
        btn.setAttribute('id','tenthbtn');
    }
    document.getElementById('options-group').appendChild(btn);
}

function optionPress(number){
    
    if(number == 1){
        var elem = document.getElementById('firstbtn');
        var txt = elem.textContent || elem.innerText;
        print(txt);
    }if(number == 2){
        var elem = document.getElementById('secondbtn');
        var txt = elem.textContent || elem.innerText;
        print(txt);
    }if(number == 3){
        var elem = document.getElementById('thirdbtn');
        var txt = elem.textContent || elem.innerText;
        print(txt);
    }if(number == 4){
        var elem = document.getElementById('fourthbtn');
        var txt = elem.textContent || elem.innerText;
        print(txt);
    }if(number == 5){
        var elem = document.getElementById('fifthbtn');
        var txt = elem.textContent || elem.innerText;
        print(txt);
    }if(number == 6){
        var elem = document.getElementById('sixthbtn');
        var txt = elem.textContent || elem.innerText;
        print(txt);
    }if(number == 7){
        var elem = document.getElementById('seventhbtn');
        var txt = elem.textContent || elem.innerText;
        print(txt);
    }if(number == 8){
        var elem = document.getElementById('eightbtn');
        var txt = elem.textContent || elem.innerText;
        print(txt);
    }if(number == 9){
        var elem = document.getElementById('ninthbtn');
        var txt = elem.textContent || elem.innerText;
        print(txt);
    }if(number == 10){
        var elem = document.getElementById('tenthbtn');
        var txt = elem.textContent || elem.innerText;
        print(txt);
    }
}

function send(){
    var elem = document.getElementById('sendbox');
    var txt = elem.value;
    elem.value = "";
    print(txt);
    
}

function print(txt){
    var elem = document.createElement('div');
    elem.textContent += txt;
    elem.setAttribute('id','usermsg');
    document.getElementById('chatbox').appendChild(elem);
    // Print to rating chatbox
    var postelem = document.createElement('div');
    postelem.textContent += txt;
    postelem.setAttribute('id','usermsg');
    document.getElementById('postchatbox').appendChild(postelem);
    reply(txt);
}

function reply(txt){
    const response = {'response':txt};
    fetch("http://127.0.0.1:5000/existing_dialogue/"+hash, 
        {
            method:'POST',
            headers: {
                'Content-type': 'application/json',
                'Accept': 'application/json'
            },
        
        body:JSON.stringify(response)}).then(res=>{
                if(res.ok){
                    console.log(res);
                    return res.json()
                }else{
                    alert("something is wrong")
                }
            }).then(jsonResponse=>{
                index++;
                let history = Object.values(jsonResponse.history[index]);
                let options = history[4];
                if(options.length == 0){
                    showForm();
                }else{
                    hideForm();
                }
                update(jsonResponse);
                if(jsonResponse.state == "evaluating"){
                    evaluate(jsonResponse);
                }
                
            } 
            ).catch((err) => console.error(err));

}


// code for the slider inputs
var slider = document.getElementById("myRange");
var output = document.getElementById("rating");
output.innerHTML = slider.value;

slider.oninput = function() {
  output.innerHTML = this.value;
}

let counter = 0;
function startScroll(){
    let id = setInterval(function(){
        counter++;
        window.scrollBy(0,2);
        if(counter == 570){
            stopScroll();
        }
    },1);
    return id;
}

function stopScroll(){
    clearInterval(scrollerId)
}

function submitRating(){
    var elem = document.getElementById("myRange");
    var rating = elem.value;
    
    const response = {'rating':rating,'index':ratingIndex};
    fetch("http://127.0.0.1:5000/existing_dialogue/"+hash, 
        {
            method:'POST',
            headers: {
                'Content-type': 'application/json',
                'Accept': 'application/json'
            },
        
        body:JSON.stringify(response)}).then(res=>{
                if(res.ok){
                    return res.json()
                }else{
                    alert("something is wrong")
                }
            }).then(jsonResponse=>{
                ratingIndex += 2;
                let history = Object.values(jsonResponse.history);
                if(ratingIndex <= history.length){
                    nextRating();
                }else{
                    finishedRating();
                }
                
                
            } 
            ).catch((err) => console.error(err));
}

function nextRating(){
    var ratingbox = document.getElementById("ratingchatbox");
    ratingbox.innerHTML = '';
    let history = Object.values(finishedDialogue.history);
    const line = history[ratingIndex-1]["line"];
    var elem = document.createElement('div');
    elem.textContent += line;
    elem.setAttribute('id','ratingmsg');
    document.getElementById('ratingchatbox').appendChild(elem);
}

function hideForm(){
    document.getElementById("sendbox").style.display="none";
    document.getElementById("submitmsg").style.display="none";
}

function showForm(){
    document.getElementById("sendbox").style.display="block";
    document.getElementById("submitmsg").style.display="block";
}

function finishedRating(){
    document.getElementById("ratingchatbox").innerHTML = '';
    document.getElementById("sliderwrapper").style.display="none";
    document.getElementById('ratingmenu').innerHTML = '';
    var elem = document.createElement('div');
    elem.textContent += "Thank you for talking to me!";
    elem.setAttribute('id','ratingmsg');
    document.getElementById('ratingchatbox').appendChild(elem);
}