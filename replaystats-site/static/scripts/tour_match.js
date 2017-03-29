var swap, swap2;


// On page exit, cache

window.onbeforeunload = function() {
	
	unmatched_replays = $(":input", "#unmatched_replays")
							.map(function() {
								return this.value
							}).toArray();
	// matches - {pairing: (replay, filter)}
	// unmatched replays - replay objects
	pairings = $("td", "#pairings_table").map(function() {
					return this.innerHTML;
				}).toArray()
				
	$.post('/update_session/', {
		"url":$("a").first().attr("href"),
		"pairings":pairings,
		"matches":$(":input", "#table-match")
							.map(function() {
								return this.value
							}).toArray(),
		"filters":$("tr", "#table-match").slice(1).map(function() {
								return $(this).attr("class");
							}).toArray(),
		"unmatched_replays":unmatched_replays,
		CSRF: getCSRFTokenValue()
		})
}

// On page load, check if stored; if not, do stuff

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