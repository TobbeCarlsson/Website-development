'use strict';


var date = new Date();
var hash = "";
var index = 0;
var scrollerId;
var ratingIndex = 3;
var finishedDialogue;
var ratedLines = [];


window.onload = function(){
    
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

//    var audioelem = document.createElement('source');
//    audioelem.setAttribute('src','http://127.0.0.1:5000/audio_feed/'+hash);
//    audioelem.setAttribute('type','audio/wav');
//    document.getElementById('audio').appendChild(audioelem);
}
 
async function update(dialogue){
    const optionsgroup = document.getElementById("options-group");
    optionsgroup.innerHTML = '';

    let history = Object.values(dialogue.history[index]);
    let options = history[4];
    let line = history[3];
    index++;
    let delay = history[5];
    let source = createAudio(history[7]);
    if(history[6]){
        const toBeRated = {'index':index, 'rated':false};
        ratedLines.push(toBeRated);
    }

    startTypingAnim();
    await sleep(delay);
    stopTypingAnim();
    if(options.length == 0){
        showForm();
    }

    removeAudio(source);

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
    const line = history[2]["line"];
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

async function reply(txt){
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
                    return res.json()
                }else{
                    alert("something is wrong")
                }
            }).then(jsonResponse=>{
                index++;
                let history = Object.values(jsonResponse.history[index]);
                let options = history[4];
                hideForm();
                update(jsonResponse);
                const delay = history[5];
                
                setTimeout(function(){ 
                    if(jsonResponse.state == "evaluating"){
                        evaluate(jsonResponse);
                    } 
                }, delay);
                
                
                
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
    for(const elem of ratedLines){
        if(elem.index == ratingIndex){
            elem.rated = true;
        }
    }
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
                console.log(jsonResponse);
                var allRated = true;
                for(const elem of ratedLines){
                    if(!elem.rated){
                        allRated = false;
                    }
                }
                if(allRated){
                    finishedRating();
                }else{
                    var missingLines = "You still have to rate line: ";
                    for(const elem of ratedLines){
                        if(!elem.rated){
                            missingLines += elem.index + ' ';
                        }
                    }
                    alert(missingLines);
                }
                
                 
            } 
            ).catch((err) => console.error(err));
}

function updateRating(){
    var ratingbox = document.getElementById("ratingchatbox");
    let history = Object.values(finishedDialogue.history);
    if(history[ratingIndex-1]["should_be_rated"]){
        ratingbox.innerHTML = '';
        const line = history[ratingIndex-1]["line"];
        var elem = document.createElement('div');
        elem.textContent += line;
        elem.setAttribute('id','ratingmsg');
        document.getElementById('ratingchatbox').appendChild(elem);
    }
}

function previousRating(){
    var elem = document.getElementById("myRange");
    var rating = elem.value;
    for(const elem of ratedLines){
        if(elem.index == ratingIndex){
            elem.rated = true;
        }
    }
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
                if(ratingIndex > 3){
                    ratingIndex -= 2;
                    updateRating();
                }else{
                    updateRating();
                }
                
                
            } 
            ).catch((err) => console.error(err));
}

function nextRating(){
    var elem = document.getElementById("myRange");
    var rating = elem.value;
    const response = {'rating':rating,'index':ratingIndex};
    for(const elem of ratedLines){
        if(elem.index == ratingIndex){
            elem.rated = true;
        }
    }
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
                
                let history = Object.values(jsonResponse.history);
                if(ratingIndex <= history.length-2){
                    ratingIndex += 2;
                    updateRating();
                }else{
                    updateRating();
                }
                
                
            } 
            ).catch((err) => console.error(err));
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
    fetch("http://127.0.0.1:5000/end_dialogue/"+hash, 
{
    method:'POST',
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
        var endLine = "Your code: " + jsonResponse.secret_code;
        alert(endLine);
} 
).catch((err) => console.error(err)); 
    document.getElementById("ratingchatbox").innerHTML = '';
    document.getElementById("sliderwrapper").style.display="none";
    document.getElementById('ratingmenu').innerHTML = '';
    var elem = document.createElement('div');
    elem.textContent += "Thank you for talking to me!";
    elem.setAttribute('id','ratingmsg');
    document.getElementById('ratingchatbox').appendChild(elem);
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
 }

function startTypingAnim(){
     // Create typing animation
     var elem = document.createElement('span');
     elem.setAttribute('class','jumping-dots');
     elem.setAttribute('id','dotswrapper')
     var dot1 = document.createElement('span');
     dot1.setAttribute('class','dot-1');
     var dot2 = document.createElement('span');
     dot2.setAttribute('class','dot-2');
     var dot3 = document.createElement('span');
     dot3.setAttribute('class','dot-3');
     dot1.textContent = '.';
     dot2.textContent = '.';
     dot3.textContent = '.';
     document.getElementById('chatbox').appendChild(elem);
     document.getElementById('dotswrapper').appendChild(dot1);
     document.getElementById('dotswrapper').appendChild(dot2);
     document.getElementById('dotswrapper').appendChild(dot3);
     chatbox.scrollTop = chatbox.scrollHeight;
}

function stopTypingAnim(){
    const elem = document.getElementById('dotswrapper');
    elem.remove();
}

function createAudio(identifier){
    const source = document.createElement('source');
    source.src = 'https://www.agnes.tv/audio_feed/' + hash + '/' + identifier + '.mp3';
    source.type = 'audio/mpeg';
    var audio = document.getElementById('audio');
    audio.appendChild(source);
    audio.play();
    return source;
}

function removeAudio(source){
    source.remove();
}