//document.getElementsByName(localStorage.getItem('openTab'))[0].click()
Window.onload = function() {
	// load clicked tab from localStorage
	console.log("test")
	document.getElementsByName(Window.localStorage.getItem('openTab'))[0].click()
};

Window.onbeforeunload = function() {
	// save clicked tab to localStorage
	Window.localStorage.setItem('openTab', 
		document.getElementsByClassName("tabLink active")[0].name);
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
	document.getElementById(tabName).style.display = "block";
	event.currentTarget.className += " active";
		//localStorage.setItem('openTab', 
		//document.getElementsByClassName("tabLink active")[0].name);
}
