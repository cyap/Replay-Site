$(document).ready(function() {
	
	$("#add-replays").click(function() {
		if ($("#replays-add").hasClass("hidden")) {
			$("#replays-add").removeClass("hidden");
		}
		else {
			$("#replays-add").addClass("hidden");
		}
	});
	
	$("#replay-text").width($("#replay-table").width());
	$("#replay-text").height($("#replay-table").height());
	
	$("#replays-add").width($("#replay-table").width());
	
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

