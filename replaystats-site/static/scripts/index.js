$(document).ready(function() {
		
	// Attach event handlers to radio buttons
	
	// Options pane
	$("#parse_types").children().click(function() {
		$("#parse_pane").children().addClass("hidden")
			.find(":input")
			.prop("disabled",true);
		$("#"+this.value).removeClass("hidden").find(":input").prop("disabled",false);
	});
	
	// Forms pane
	$(".stats.form").find(":radio").click(function() {
		$(this).siblings(".rawtext").attr("name", "stats_" + $(this).val())
	});
	
	// Add more button
	$("#stats_more").on("click", function() {
		// Clone div and reset textarea
		var clone = $(".stats.form:last").clone(true);
		clone.find("textarea").val("");
		// Rename input
		clone.find("input").attr("name", function() {
			return $(this).attr("name").slice(0,-1) 
			+ String(parseInt($(this).attr("name").slice(-1)) + 1)
		});
		clone.insertBefore($("#stats_more"));
	});
	
	// On form input
	$("#thread_tiers").on("input", function(event) {
		$("#thread_title").val(event.target.value)
	});
	
	$("#thread_button").click()
	$(".stats.form").find(":radio:first").click()
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


