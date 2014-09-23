// Initialize global date objects and set them by default
// to yesterday's date. 
d = new Date();
d.setDate( d.getDate() - 1 );
var startDate = d.getFullYear() + "-" + (d.getMonth() + 1) + "-" + d.getDate();
var endDate = startDate;
var startTime = "00:00";
var endTime = "23:59";



$(window).load(function(){
	// Check to see if URL has fun things for us
	
	startDate = (getQueryVariable("startdate") != false ? getQueryVariable("startdate") : startDate);
	endDate = (getQueryVariable("enddate") != false ? getQueryVariable("enddate") : startDate);
	startTime = (getQueryVariable("starttime") != false ? getQueryVariable("starttime") : startTime);
	endTime = (getQueryVariable("endtime") != false ? getQueryVariable("endtime") : endTime);

	// Initialize map and add Stamen map layer
	var layer = new L.StamenTileLayer("terrain");
	var map = new L.Map("map", {
		center: new L.LatLng(40.4417, -80.0000),
		zoom: 13,
		minZoom: 12,
		zoomControl:false
	});
		
	map.addLayer(layer);
	
	new L.control.zoom({position: "bottomright"}).addTo(map);
	
	// Initialize markers object
	var markers = L.markerClusterGroup();
	
	// Pull data
	$.getJSON("py/process.py?operation=getIncidents&startDate=" + startDate + "&endDate=" + endDate + "&startTime=" + startTime + "&endTime=" + endTime, function(data){
		
		// Update total count
		$("#total_incidents").html( data.length );
		
		$.each(data, function(i, incident){
			
			// Add new incident module
			var newIncident = $("<div class = 'incident'></div>").appendTo("#incident_list");
			
			// Properly class incident module as Arrest or Offense
			newIncident.addClass( (incident["type"] == "ARREST" ? "arrest" : "offense" ) ); 
			
			// Add timestamp
			newIncident.append("<div class = 'timestamp'>" + incident["time"] + " &mdash; " + incident["type"] + " </div>");
			
			// Add charges module
			var charges = $("<div class = 'charges'></div>").appendTo(newIncident);
			
			// Cycle through crimes
			$.each(incident.charges, function(j, crime){
				
				// Add crime to listing
				charges.append("<h1>" + crime.description + "</h1>");
				
			});
			
			// Add info module
			var info = $("<div class='info'></div>").appendTo(newIncident);
			
			// Add location and perp info (if applicable) to info module
			info.append("<table><tr><td><i class='fa fa-map-marker'></td><td><h2>" + incident.neighborhood + "</h2><h2>" + incident.address + "</h2></td>");
			if( incident["type"] == "ARREST" ) info.find("tr").after("<tr><td><i class='fa fa-user'></i></td><td><h2>" + incident.age + "-year-old " + (incident.gender == "M" || incident.gender == "F" ? ( incident.gender == "M" ? "man" : "woman" ) : "person of unknown gender") + "</h2></td></tr>");
			
			// Add marker
			var marker = L.marker([incident.lat, incident.lng]);
			
			// Scroll to and highlight incident on marker click
			marker.on("click", function(){
				// Check if list is hidden; act accordingly
				$("#content").removeClass("hidden");
				$("#content").scrollTo( newIncident, 250, {offset:-50} );
				$(".incident").removeClass("selected");
				newIncident.addClass("selected");
				
			});
			
			// "Hover" highlight incident on marker mouseover
			marker.on("mouseover", function(){
				newIncident.addClass("hover");
			});
			
			marker.on("mouseout", function(){
				newIncident.removeClass("hover");
			});
			
			// Add marker to markers group
			markers.addLayer(marker);
			
			// Zoom to marker on incident click
			newIncident.click(function(){
				map.setView([incident.lat, incident.lng], 17, {animate:true});
				$(".incident").removeClass("selected");
				newIncident.addClass("selected");
			});
			
		});
					
		// Size sidebar
		resize();
		
		// Add markers to map
		map.addLayer(markers);
		
		// Add aggregrated charges
		$.getJSON("py/process.py?operation=getAggregate&startDate=" + startDate + "&endDate=" + endDate + "&startTime=" + startTime + "&endTime=" + endTime, function(data){
			$.each(data, function(j, aggregateCrime){
				var newAggregateCrime = $("<tr></tr>").appendTo("#aggregate table");
				newAggregateCrime.append("<td><strong>" + aggregateCrime.description + "</strong></td>");
				newAggregateCrime.append("<td>" + aggregateCrime.total + "</td>");
			});
		});
		
		// slide out 1.5 seconds after loading
		setTimeout(function(){ 
			$("#content, #header").removeClass("hidden");
		}, 1500) 
	
	});
	
	
	
	// 
	// Global events
	//
	
	$(window).on("resize", resize);
	
	$(".buttonContainer").children().click(function(){
		attr = $(this).attr("to");
		if (typeof attr !== typeof undefined && attr !== false) {
			$(".popout").not("#" + attr).addClass("hidden");
			$("#" + attr).toggleClass("hidden");
		}
	});
	
	
});

function resize(){
	// Resize height of sidebar shadow (and sidebar)
	$("head").append("<style type = 'text/css'>#content:after{ height: " + $("#content").height() + "px }</style>");
	$("#content").css("height", "100%");
	$("#content").css("height", $(window).height() - $("#header").height()-40); // sorry about using 40px, its arbitrary but works
		
}

function getQueryVariable(variable){
	var query = window.location.search.substring(1);
	var vars = query.split("&");
	for (var i=0;i<vars.length;i++) {
			var pair = vars[i].split("=");
			if(pair[0] == variable){return pair[1];}
	}
	return(false);
}