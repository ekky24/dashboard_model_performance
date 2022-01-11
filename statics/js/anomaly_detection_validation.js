$(document).ready(function() {
    /* ***************************************** */
	/* VARIABLE AND FUNCTION DEFINITIONS */

    function fetch_anomaly_detection_validation_data() {
        unit_value = $('#select-unit').val();
        equipment_value = $('#select-equipment').val();
        system_value = $('#select-system').val();
        tag_value = $('#select-tags').val();
        date_range_value = $('#date-range-picker').val(); 

        if(tag_value != "" && date_range_value != "") {
            $('#loading-modal').modal({
                show: true,
                backdrop: 'static', 
                keyboard: false
            });

            $.ajax({url: "/get_anomaly_detection_validation_data",
            data: {'unit': String(unit_value), 
                'equipment': String(equipment_value), 
                'system': String(system_value), 
                'tag': String(tag_value), 
                'date_range': String(date_range_value)}, 
            success: function(data){
                if(data.status == 'failed') {
                    alert('FAILED!!\n\n' + data.data)
                }
                else if(data.status == 'success') {
                    $('.intro-text').remove();

                    index_data = data.data.realtime.index;
                    realtime_data = data.data.realtime.data;
                    autoencoder_data = data.data.autoencoder.data;
                    lower_limit_data = data.data.lower_limit.data;
                    upper_limit_data = data.data.upper_limit.data;
                    tags = data.data.tags;

                    parse_anomaly_lower = JSON.parse(data.data.anomaly_lower);
                    parse_anomaly_upper = JSON.parse(data.data.anomaly_upper);
                    anomaly_lower_data = parse_anomaly_lower.data;
                    anomaly_upper_data = parse_anomaly_upper.data;

                    $('#card-body-anomaly').empty()
                    for (let tag_index = 0; tag_index < tags.length; tag_index++) {
                        tag_id = "anomaly-graph-" + tag_index
                        $('#card-body-anomaly').append("<div id='" + tag_id + "'></div>");

                        realtime_graph_data = [];
                        autoencoder_graph_data = [];
                        lower_limit_graph_data = [];
                        upper_limit_graph_data = [];
                        anomaly_lower_graph_data = [];
                        anomaly_upper_graph_data = [];
                        index_graph_data = [];

                        for (let index = 0; index < realtime_data.length; index++) {
                            realtime_graph_data.push(realtime_data[index][tag_index]);
                            autoencoder_graph_data.push(autoencoder_data[index][tag_index]);
                            lower_limit_graph_data.push(lower_limit_data[index][tag_index]);
                            upper_limit_graph_data.push(upper_limit_data[index][tag_index]);
                            anomaly_lower_graph_data.push(anomaly_lower_data[index][tag_index]);
                            anomaly_upper_graph_data.push(anomaly_upper_data[index][tag_index]);
                            index_graph_data.push(new Date(index_data[index]));
                        } 

                        /* Plotting Control Limits */
                        var control_limit_graph = [
                            {
                                x: index_graph_data,
                                y: realtime_graph_data,
                                type: 'scatter',
                                name: 'Actual',
                                marker: {
                                    color: 'rgba(2, 117, 216, 0.95)'
                                }
                            },
                            {
                                x: index_graph_data,
                                y: lower_limit_graph_data,
                                type: 'scatter',
                                name: 'Lower Limit',
                                fill: 'tonextx', 
                                fillcolor: 'rgba(50, 168, 82, 0.05)',
                                marker: {
                                    color: 'rgba(50, 168, 82, 0.95)'
                                }
                            },
                            {
                                x: index_graph_data,
                                y: upper_limit_graph_data,
                                type: 'scatter',
                                name: 'Upper Limit',
                                fill: 'tonextx', 
                                fillcolor: 'rgba(50, 168, 82, 0.15)',
                                marker: {
                                    color: 'rgba(50, 168, 82, 0.95)'
                                }
                            },
                            {
                                x: index_graph_data,
                                y: anomaly_lower_graph_data,
                                type: 'scatter',
                                name: 'Anomaly Lower',
                                mode: 'markers',
                                marker: {
                                    color: 'rgba(231, 74, 59, 1)',
                                    size: 10,
                                }
                            },
                            {
                                x: index_graph_data,
                                y: anomaly_upper_graph_data,
                                type: 'scatter',
                                name: 'Anomaly Upper',
                                mode: 'markers',
                                marker: {
                                    color: 'rgba(231, 74, 59, 1)',
                                    size: 10,
                                }
                            },
                        ];

                        var control_limit_layout = {
                            title: tags[tag_index],
                            xaxis: {
                                type: 'date',
                                tick0: index_graph_data,
                                tickmode: 'linear',
                                dtick: 24*60*60*1000,
                            },
                            yaxis: {
                                showline: false
                            },
                            showlegend: false
                        };
                        Plotly.newPlot(tag_id, control_limit_graph, control_limit_layout);
                    }
                }
            }}).done(function() {
                $('#loading-modal').modal('hide');
            });
        }
    }

    /* ***************************************** */

    // If current page is anomaly validation, then disable selects
    $(".navbar-select-tag").remove()
    $(".navbar-select-bad-model-time-interval").remove()

    /* Nav Items Configuration */
    $('.nav-item').removeClass("active");
    $('#nav-group-anomaly-detection').addClass("active");
    $('#nav-validation-anomaly-detection').addClass("active");

    $('#select-tags').on('change', fetch_anomaly_detection_validation_data);
    $('#date-range-picker').on('apply.daterangepicker', fetch_anomaly_detection_validation_data);

    $('#select-tags').select2({
        placeholder: "Select multiple options",
    });
});