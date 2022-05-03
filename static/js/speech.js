var synth = window.speechSynthesis;

var pitchValue = 1;
var rateValue = 1;

voices = synth.getVoices().sort(function (a, b) {
    const aname = a.name.toUpperCase(), bname = b.name.toUpperCase();
    if ( aname < bname ) return -1;
    else if ( aname == bname ) return 0;
    else return +1;
});

function speak(text){
    if (synth.speaking) {
        console.error('speechSynthesis.speaking');
        return;
    }
    if (text !== '') {
        var utterThis = new SpeechSynthesisUtterance(text);
        utterThis.onend = function (event) {
            console.log('SpeechSynthesisUtterance.onend');
        }
        utterThis.onerror = function (event) {
            console.error('SpeechSynthesisUtterance.onerror');
        }
        utterThis.voice = voices[Math.floor(Math.random() * 2)];
        utterThis.pitch = pitchValue;
        utterThis.rate = rateValue;
        synth.speak(utterThis);
    }
}
