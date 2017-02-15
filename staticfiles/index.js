function openTab(event, tabName) {
	/* Based on w3schools implementation of tabs */
	
	// TODO: localstorage
	// on document load - get preferences
	// open saved tab

	// Get all elements with class="tabcontent" and hide them
	Array.prototype.forEach.call(document.getElementsByClassName("tabContent"), function(tabContent) {
		tabContent.style.display = "none";
	});
	
	
	// Get all elements with class="tablinks" and remove the class "active"
	Array.prototype.forEach.call(document.getElementsByClassName("tabLink"), function(tabLink) {
		tabLink.className = tabLink.className.replace(" active", "");
	});

	// Show the current tab, and add an "active" class to the link that opened the tab
	document.getElementById(tabName).style.display = "block";
	event.currentTarget.className += " active";
}
