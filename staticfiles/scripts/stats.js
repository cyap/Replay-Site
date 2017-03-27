$(document).ready(function() {
	
	// Options pane
	$(".tab").click(function() {
		$("#"+$(this).attr("name")).removeClass("hidden");
		//.find(":input").prop("disabled",false)
		
		$("#"+$(this).siblings(".tab").attr("name")).addClass("hidden");
		//.find(":input").prop("disabled",true);
	});
	
	$("#replay-text").width($("#replay-listing").width());
	$("#replay-text").height($("#replay-listing").height());
	$("[name=replay-listing]").click();
})