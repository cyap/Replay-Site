var swap, swap2;

function dropFunc(obj) {
	// swap two
	//event.target = event
	swap2 = event.target.parentNode;
	position = swap2.nextSibling;
	swap.parentNode.insertBefore(swap2, swap)
	position.parentNode.insertBefore(swap, position)
	
};

function overFunc() {
    event.preventDefault();
};

function pickFunc() {
	swap = event.target.parentNode
	//dragged = event.target;
    //event.dataTransfer.setData("picked", event.target.id);
}

/* TODO 
- Swap from unmatched replays table
- Round markers on table
- Separate pairings from replay matches
	- DONE: formatting
- Implement advanced stats
- Format name
- Move all logic to .js
*/