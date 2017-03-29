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
	
	/*
	// Post button
	$("#post_button").click(function() {
		
		
		$.post('/update_stats/', {
			"rep_submit":true,
			"replay_urls":["http://replay.pokemonshowdown.com/smogtours-gen4ou-234660"]
		})
	});*/
})

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

var csrftoken = getCookie('csrftoken');

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

