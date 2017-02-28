window.onload = function() {
	// load clicked tab from localStorage
	// update save
	try {
		document.getElementsByName(localStorage.getItem("openTab"))[0].click();
	}
	catch(e) {
		document.getElementsByName("threadTab")[0].click();
	}
	
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
};

window.onbeforeunload = function() {
	// save clicked tab to localStorage
	try {
		localStorage.setItem("openTab", 
			document.getElementsByClassName("tabLink active")[0].name);
	}
	catch(e) {
		return;
	}
}

function openTab(event, tabName) {
	/* Based on w3schools implementation of tabs */
	
	// Get all elements with class="tabcontent" and hide them
	Array.prototype.forEach.call(document.getElementsByClassName("tabContent"),
		function(tabContent) {
			tabContent.style.display = "none";
		});
	
	
	// Get all elements with class="tablinks" and remove the class "active"
	Array.prototype.forEach.call(document.getElementsByClassName("tabLink"),
		function(tabLink) {
			tabLink.className = tabLink.className.replace(" active", "");
		});

	// Show the current tab, and add an "active" class to the link that opened the tab
	// Add x
	//if (event.currentTarget.className.endsWith(" active")) {
	//	document.getElementById(tabName).style.display = "none";
	//	event.currentTarget.className -= " active";
	//}
	//else {
		document.getElementById(tabName).style.display = "block";
		event.currentTarget.className += " active";
	//}
}


