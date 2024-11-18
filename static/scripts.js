

function drawMap(location, data, selectedIndex) {
    var map = L.map('map').setView([location.lat, location.lot], 17);

    const roi1Data = data.filter(item => item.area === 'roi1' && item.band_name === selectedIndex)[0];
    const roi2Data = data.filter(item => item.area === 'roi2' && item.band_name === selectedIndex)[0];

    var roi1Layer = L.tileLayer(roi1Data.map_url, {
        maxZoom: 19,
        attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    });

    var roi2Layer = L.tileLayer(roi2Data.map_url, {
        maxZoom: 19,
        attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    });

// Add the base map layer
    var baseLayer = L.tileLayer('http://mt0.google.com/vt/lyrs=s&hl=ko&x={x}&y={y}&z={z}', {
        attribution: '&copy; Google'
    }).addTo(map);

    roi1Layer.addTo(map);
    roi2Layer.addTo(map);


    var overlayMaps = {
        "ROI 1": roi1Layer,
        "ROI 2": roi2Layer
    };

    L.control.layers(null, overlayMaps, {collapsed: false}).addTo(map);

}

function drawChart(data, selectedIndex) {
    // Separate data by area
    const roi1Data = data.filter(item => item.area === 'roi1');
    const roi2Data = data.filter(item => item.area === 'roi2');

    const roi1Trace = {
        x: roi1Data.map(item => item.date),
        y: roi1Data.map(item => item[selectedIndex]),
        mode: 'lines+markers',
        name: 'ROI1',
        line: {color: 'blue'},
        marker: {color: 'blue'}
    };

    const roi2Trace = {
        x: roi2Data.map(item => item.date),
        y: roi2Data.map(item => item[selectedIndex]),
        mode: 'lines+markers',
        name: 'ROI2',
        line: {color: 'green'},
        marker: {color: 'green'}
    };

    // Layout configuration
    const layout = {
        title: `${selectedIndex} Time Series`,
        xaxis: {title: 'Date'},
        yaxis: {title: selectedIndex},
        margin: {l: 50, r: 50, t: 50, b: 50}
    };

    // Render the chart
    Plotly.newPlot('plotly-chart', [roi1Trace, roi2Trace], layout);
}

$("#fetchDataBtn").click(function () {
    var selectedImage = $("#image_name").val();
    var selectedRegion = $("#station_name").val();
    var startDate = $("#start_date").val();
    var endDate = $("#end_date").val();

    $("#loader").show();


    $.ajax({
        url: "/load-data",
        method: "GET",
        data: {
            image_name: selectedImage,
            station_name: selectedRegion,
            start_date: startDate,
            end_date: endDate
        },
        success: function (response) {

            $("#loader").hide();

            responseData = response;

            // Optionally, draw the chart and map with the default index (e.g., NDVI)
            var selectedIndex = $("#index_name").val();

            drawChart(response.value_data, selectedIndex);
            drawMap(response.location, response.image_data, selectedIndex);
                        // drawMap(response.location, response.image_data);


        },
        error: function () {

            $("#loader").hide();
            alert('Error fetching data');
        }
    });
});
$(document).ready(function () {
    $('#index_name').select2({
        placeholder: 'Select Vegetation Index',
        allowClear: true
    });

    $('#image_name').select2({
        placeholder: 'Select Image',
        allowClear: true
    });
});

$("#index_name").change(function () {
    if (responseData) {
        var selectedIndex = $(this).val();

        drawChart(responseData.value_data, selectedIndex);
        drawMap(responseData.location, responseData.image_data, selectedIndex);
        // drawMap(responseData.location, responseData.image_data,);

    }
});