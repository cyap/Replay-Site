$(document).ready(function() {
		
	// Attach event handlers to radio buttons
	
	
	// Options pane
	$(".tab").click(function() {
		$("#"+$(this).attr("name")).removeClass("hidden");
		//.find(":input").prop("disabled",false)
		
		$("#"+$(this).siblings(".tab").attr("name")).addClass("hidden");
		//.find(":input").prop("disabled",true);
	});
	
	$("[name=replay-listing]").click();
})