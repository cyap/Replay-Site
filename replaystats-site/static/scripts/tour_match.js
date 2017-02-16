function dropFunc(obj) {
	// swap two
	//event.target = event
	console.log(event.target)
	//console.log(event.dataTransfer)
	console.log(event.dataTransfer.getData("picked"))
};

function overFunc() {
    event.preventDefault();
};

function pickFunc() {
    event.dataTransfer.setData("picked", event.target.id);
}