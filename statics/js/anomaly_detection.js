$(document).ready(function() {
    /* ***************************************** */
	/* VARIABLE AND FUNCTION DEFINITIONS */

    function fetch_anomaly_detection_data() {
        tag_value = $('#select-tag').val();
        unit_value = $('#select-unit').val();
        date_range_value = $('#date-range-picker').val();

        if(tag_value != "" && date_range_value != "") {
            $('#loading-modal').modal({
                show: true,
                backdrop: 'static', 
                keyboard: false
            });

            $.ajax({url: "/get_anomaly_detection_data",
            data: {'unit': String(unit_value), 'tag': String(tag_value), 'date_range': String(date_range_value)}, 
            success: function(data){
                $('.intro-text').remove();

                index_data = data.data.realtime.index;
                realtime_data = data.data.realtime.data;
                autoencoder_data = data.data.autoencoder.data;
                lower_limit_data = data.data.lower_limit.data;
                upper_limit_data = data.data.upper_limit.data;

                metrics_data = data.data.metrics.data;
                metrics_index = data.data.metrics.index;
                metrics_ovr_loss = data.data.metrics.ovr_loss;
                
                realtime_graph_data = [];
                autoencoder_graph_data = [];
                lower_limit_graph_data = [];
                upper_limit_graph_data = [];

                for (let index = 0; index < realtime_data.length; index++) {
                    realtime_graph_data.push(realtime_data[index][0]);
                    autoencoder_graph_data.push(autoencoder_data[index][0]);
                    lower_limit_graph_data.push(lower_limit_data[index][0]);
                    upper_limit_graph_data.push(upper_limit_data[index][0]);
                } 
                
                /* Plotting Autoencoder Performance */
                var autoencoder_graph = [
                    {
                        x: index_data,
                        y: realtime_graph_data,
                        type: 'scatter',
                        name: 'Actual',
                        marker: {
                            color: 'rgba(2, 117, 216, 0.95)'
                        }
                    },
                    {
                        x: index_data,
                        y: autoencoder_graph_data,
                        type: 'scatter',
                        name: 'Prediction',
                        marker: {
                            color: 'rgba(50, 168, 82, 0.95)'
                        }
                    }
                ];

                var autoencoder_layout = {
                    title: data.data.realtime.columns[0],
                    yaxis: {
                        showline: false
                    },
                    showlegend: false
                };
                Plotly.newPlot('autoencoder-graph', autoencoder_graph, autoencoder_layout);

                /* Plotting Control Limits */
                var control_limit_graph = [
                    {
                        x: index_data,
                        y: realtime_graph_data,
                        type: 'scatter',
                        name: 'Actual',
                        marker: {
                            color: 'rgba(2, 117, 216, 0.95)'
                        }
                    },
                    {
                        x: index_data,
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
                        x: index_data,
                        y: upper_limit_graph_data,
                        type: 'scatter',
                        name: 'Upper Limit',
                        fill: 'tonextx', 
                        fillcolor: 'rgba(50, 168, 82, 0.15)',
                        marker: {
                            color: 'rgba(50, 168, 82, 0.95)'
                        }
                    }
                ];

                var control_limit_layout = {
                    title: data.data.realtime.columns[0],
                    yaxis: {
                        showline: false
                    },
                    showlegend: false
                };
                Plotly.newPlot('control-limit-graph', control_limit_graph, control_limit_layout);

                /* Plotting Metrics */
                var metrics_graph = [
                    {
                        x: metrics_index,
                        y: metrics_data,
                        type: 'scatter',
                        name: 'Loss',
                        marker: {
                            color: 'rgba(2, 117, 216, 0.95)'
                        }
                    },
                ];

                var metrics_layout = {
                    title: data.data.realtime.columns[0],
                    yaxis: {
                        showline: false
                    },
                    showlegend: false
                };
                Plotly.newPlot('metrics-graph', metrics_graph, metrics_layout);

                $('#ovr-metric-value').text(metrics_ovr_loss);
	            $('.metrics-caption').css('visibility', 'visible');
            }}).done(function() {
                $('#loading-modal').modal('hide');
            });
        }
    }

    /* ***************************************** */

    /* Nav Items Configuration */
    $('.nav-item').removeClass("active");
    $('#nav-anomaly-detection').addClass("active");

    $('#select-tag').on('change', fetch_anomaly_detection_data);
    $('#date-range-picker').on('apply.daterangepicker', fetch_anomaly_detection_data);
});