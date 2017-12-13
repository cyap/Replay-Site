var swap1, swap2;

$(document).ready(function() {
	// Allow for rearranging rows
	$(".dragHandler")
	.prop("tabindex", "0")
	.on({
		dragstart: function pickFunc() {
			// Store pickup target as global variable
			swap1 = event.target;
		},
		dragover: function overFunc() {
    		event.preventDefault();
		},
		drop: function dropFunc() {
			swap2 = event.target.parentNode;
			swapRows(swap1, swap2);
		},
		blur: function blurFunc() {
			// If row loses focus and is not being swapped with another row, 
			// remove from ongoing swap
			if (!event.relatedTarget || 		
				!event.relatedTarget.classList.contains("dragHandler")) {
					swap1 = undefined;
				}
		},
		focus: function selectFunc() {
			if (swap1) {
				swap2 = document.activeElement;
				swapRows(swap1, swap2);
			}
			else {
				swap1 = document.activeElement;
			}
		}
	});
});


// On page exit, cache

window.onbeforeunload = function() {
	return "Are you sure? You didn't finish the form!";
	
	unmatched_replays = $(":input", "#unmatched_replays")
							.map(function() {
								return this.value
							}).toArray();
	// matches - {pairing: (replay, filter)}
	// unmatched replays - replay objects
	pairings = $("td", "#pairings_table")
				.map(function() {
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
		"csrfmiddlewaretoken":CSRF
		})
}

function swapRows(row1, row2) {
	if (row1 !== row2) {
		position = row2.nextSibling;
		row1.parentNode.insertBefore(row2, row1);
		position.parentNode.insertBefore(row1, position);
		swap1 = swap2 = undefined;
	}
}

/* TODO 
- Round markers on table
- Separate pairings from replay matches
	- DONE: formatting
- Implement advanced stats
*/