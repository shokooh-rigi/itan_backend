let inputs = document.getElementsByTagName('input');
for (let index = 0; index < inputs.length; ++index) {
    console.log('here');
    if (inputs[index].value === 'Next') {
        inputs[index].setAttribute("title", "Not Available for Demo");
        inputs[index].setAttribute("data-content", "Contact sales department for more information.");
        inputs[index].setAttribute("data-toggle", "popover");
        inputs[index].removeAttribute("type");
    }
}