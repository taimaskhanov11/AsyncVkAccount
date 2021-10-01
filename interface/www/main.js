var allProc = 0
var check = false //todo


eel.expose(addText);
eel.expose(test);
eel.expose(AddVersion);
eel.expose(createDiv);
eel.expose(updateDiv);
eel.expose(changeText);
eel.expose(giveAvatar)

function addText(text, color) {

    let ul = document.getElementById('content1');
    // let liObj = document.createElement("li");
    // liObj.className = "list-group-item group-item";
    // // liObj.className = "group-item";
    // liObj.id = 'grad'
    // // v1.style.backgroundColor = 'rgb(231,234,237)'
    // liObj.innerHTML = text
    // // console.log(color)
    // liObj.style.color = color
    if (ul.childNodes.length > 100) { //todo

        let listItems = ul.getElementsByTagName("li");
        let last = listItems[listItems.length - 1];
        // ul.parentNode.removeChild(last);
        ul.removeChild(last);
        // let oldObj = document.getElementById('grad');
        // ul.removeChild(oldObj);
    }
    // ul.appendChild(liObj)
    let liObj = `<li class='list-group-item group-item' id="grad" style="top:8.5em"'>${text}</li>`;
    // let liObj = `<li class='list-group-item group-item' id="grad" style='color: ${color}'> ${text}</li>`;//todo
    ul.insertAdjacentHTML('afterbegin', liObj);
    // ul.insertAdjacentHTML('beforeend', liObj);
    // let lst = document.getElementById(grId);
    // console.log(lst)
    if (check === true) {
        window.scrollTo(0, document.body.scrollHeight);
    }


    if (allProc < 100) {
        let status = document.getElementById('status-bar');

        let endProg = String(allProc) + '%';
        status.style.width = endProg
        status.setAttribute('aria-valuenow', endProg)
        status.innerHTML = 'Загрузка ' + endProg;
        // console.log(status.getAttribute('aria-valuenow'))
        if (allProc === 99) {
            var divElement = document.getElementById('progress');
            divElement.remove()
        }
        allProc += 1

    }

}


function turnScroll() {
    var button = document.getElementById('btn-scroll');

    if (check === true) {
        check = false;
        button.innerHTML = 'Auto-scroll OFF';
        button.className = "btn btn-outline-danger btn-sm";
        window.scrollTo(0, 0);
    } else {
        check = true;
        button.innerHTML = 'Auto-scroll ON';
        button.className = "btn btn-outline-success btn-sm";

    }
}


function changeButtonColor(color, id) {
    let button = document.getElementById(id);

    console.log(button.className.indexOf('secondary'))
    if (button.className.indexOf('secondary') > 0) {
        let colorName = `btn btn-${color} third`
        console.log(1)
        button.className = colorName

    } else {
        let colorName = `btn btn-outline-secondary third`
        console.log(colorName)
        button.className = colorName

    }

}


const windowData = {
    'numbers': eel.window_return,
    'users': eel.window_return,
    'unusers': eel.window_return,
}


function updateDiv(text, elementId) {
    let oldElem = document.getElementById(elementId)
    oldElem.insertAdjacentHTML('beforeend', text);

}

function changeText(text, elementId) {
    let oldElem = document.getElementById(elementId)
    oldElem.text = text
}


function createDiv(x = 'numbers') {
    // let dynamicHeight = Math.ceil(Math.random() * 100) + 40;
    let oldElem = document.getElementById("elem0")
    if (oldElem) {
        console.log(oldElem)
        oldElem.remove()
    }
    eel.window_return(x)(function (oldElemContent) {
        console.log(oldElemContent)
        let newElem = `<div class='elem' id="elem0" style='--h: 30em'> ${oldElemContent}</div>`;
        let elements = document.getElementById("content-div");
        elements.insertAdjacentHTML("afterbegin", newElem);
    })
    // eel.window_return()(function (oldElemContent) {
    //     console.log(oldElemContent)
    //     let newElem = `<div class='elem' id="elem0" style='--h: 30em'> ${oldElemContent}</div>`;
    //     let elements = document.getElementById("content-div");
    //     elements.insertAdjacentHTML("afterbegin", newElem);
    // })
    //

}


// let button = document.getElementById("content-div")
// button.addEventListener("click", createDiv);

function createDiv1() {
    let div = document.createElement("div");
    // div.style.width = "100px";
    // div.style.height = "100px";
    div.className = 'content-div-child'
    div.style.background = "red";
    div.style.color = "white";
    div.innerHTML = "Hello";

    document.getElementById("content-div").appendChild(div);


}

function test() {
    return 'BOOM!'
}

function AddVersion(version) {
    let doc = document.getElementById('text2');
    doc.style.color = 'blue';
    doc.style.fontSize = '2em';
    doc.innerHTML = `${version}<div class="text-left img_preview">
                    <img src="media/favicon.ico" alt="Fancy" id="photo2"></div>`;
    doc.style.paddingLeft = '2em';
    doc.style.paddingTop = '1em';
}

// avatarInfo =
function giveAvatar(path) {
    let photo = document.getElementById('photo1-container')
    console.log(path)
    photo.innerHTML = `<img src="media/${path}" alt="Fancy" id="photo1">`

}
//
//
// }

