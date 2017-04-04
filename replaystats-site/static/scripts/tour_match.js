var swap1, swap2;

$(document).ready(function() {
	// Allow for rearranging rows
	$(".dragHandler")
	.attr("ondragstart", "pickFunc()")
	.attr("ondragover", "overFunc()")
	.attr("ondrop", "dropFunc(this)")
	.attr("onfocus","selectFunc(this)")
	.attr("onblur","blurFunc(this)")
	.prop("tabindex", "0");
});


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
		"csrfmiddlewaretoken": CSRF
		})
}

function swapRows(row1, row2) {
	position = row2.nextSibling;
	row1.parentNode.insertBefore(row2, row1);
	position.parentNode.insertBefore(row1, position);
	swap1 = swap2 = undefined;
}

function dropFunc(obj) {
	swap2 = event.target.parentNode;
	// Swap rows
	swapRows(swap1, swap2);
	
};

function overFunc() {
    event.preventDefault();
};

function pickFunc() {
	// Store pickup target as global variable
	swap1 = event.target.parentNode;
}

function selectFunc(dragHandler) {
	if (swap1) {
		swap2 = document.activeElement.parentNode;
		swapRows(swap1, swap2);
	}
	else {
		swap1 = document.activeElement.parentNode;
	}
}

function blurFunc(dragHandler) {
	// If row loses focus and is not being swapped with another row, 
	// remove from ongoing swap
	if (!event.relatedTarget || event.relatedTarget.className !== "dragHandler") {
		swap1 = undefined;
	}
}


/* TODO 
- Round markers on table
- Separate pairings from replay matches
	- DONE: formatting
- Implement advanced stats
*/