
	/*try {
	document.getElementById("form_pane").insertAdjacentHTML("afterbegin", localStorage.getItem("filled_form"))
	}
	catch(e) {
		console.log("failed");}*/
$(document).ready(function() {
		
	// Attach event handlers to radio buttons
	$("#parse_types").children().each(function() {
		$(this).click(function() {
			$("#parse_pane").children().each(function() {
				$(this).addClass("hidden");
				$(":input", this).each(function() {
					$(this).prop("disabled", true);
				});
			});
			$("#"+this.value).removeClass("hidden")
			$(":input","#"+this.value).each(function() {
				$(this).prop("disabled", false);
			});
		});
	});
	
	// Add more button
	$("#stats_more").on("click", function() {
		//$("#stats_pane").append($("#stats_form").clone());
		$("#stats_form").clone().insertBefore($("#stats_more"));
	})
	
	// On form input
	$("#thread_tiers").on("input", function(event) {
		$("#thread_title").val(event.target.value)
	});
	
	$("#thread_button").click()
});
	
				
				
									   

	
	//document.getElementById("thread_button").click()
	/*
	// Function to fill in search
	Array.prototype.forEach.call(document.getElementsByClassName("tier_input"),
	function(field) {
		field.oninput = function() {
			// If value ends in comma
			if (field.value.slice(-1) == ",") {
				// Store as filter
				// TODO: styling
				filter = document.createElement("span");
				filter.textContent = field.value.slice(0,-1)
				filter.className = "tier_filter"
				field.parentNode.insertBefore(filter, field)
				// Insert x: field.parentNode.insertBefore(
				field.value = ""
				// TODO: Change to accept hidden input
			}
		
	});*/

window.onbeforeunload = function() {
	// Save form / option to local storage
	try {
		localStorage.setItem("filled_form",
			document.getElementById("form_pane").innerHTML)
	}
	catch(e) {
		return;
	}
}


