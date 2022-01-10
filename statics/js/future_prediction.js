$(document).ready(function() {
    /* ***************************************** */
	/* VARIABLE AND FUNCTION DEFINITIONS */

    function fetch_future_prediction_data() {
        tag_value = $('#select-tag').val();
        unit_value = $('#select-unit').val();
        date_range_value = $('#date-range-picker').val();

        if(tag_value != "" && date_range_value != "") {
            $('#loading-modal').modal({
                show: true,
                backdrop: 'static', 
                keyboard: false
            });
            
            $.ajax({url: "/get_future_prediction_data",
            data: {'unit': String(unit_value), 'tag': String(tag_value), 'date_range': String(date_range_value)}, 
            success: function(data){
                if(data.status == 'failed') {
                    alert('FAILED!!\n\n' + data.data)
                }
                else if(data.status == 'success') {
                    $('.intro-text').remove();

                    index_data = data.data.prediction.data.index;
                    prediction_data = data.data.prediction.data.data;
                    input_step = data.data.prediction.input_step;
                    tag_name = data.data.prediction.tag_name;

                    metrics_data = data.data.metrics.data;
                    metrics_index = data.data.metrics.index;
                    metrics_ovr_loss = data.data.metrics.ovr_loss;

                    realtime_graph_data = [];
                    prediction_graph_data = [];
                    index_graph_data = [];
                    metrics_graph_index = [];
                    
                    for (let index = 0; index < prediction_data.length; index++) {
                        realtime_graph_data.push(prediction_data[index][0]);
                        prediction_graph_data.push(prediction_data[index][1]);
                        index_graph_data.push(new Date(index_data[index]));
                    } 

                    for (let index = 0; index < metrics_data.length; index++) {
                        metrics_graph_index.push(new Date(metrics_index[index]));
                    } 

                    /* Plotting Prediction Plot */
                    var future_prediction_graph = [
                        {
                            x: index_graph_data.slice(0, input_step),
                            y: realtime_graph_data.slice(0, input_step),
                            type: 'scatter',
                            name: 'Actual',
                            marker: {
                                color: 'rgba(2, 117, 216, 0.95)'
                            }
                        },
                        {
                            x: index_graph_data.slice(input_step-1, prediction_graph_data.length),
                            y: prediction_graph_data.slice(input_step-1, prediction_graph_data.length),
                            type: 'scatter',
                            name: 'Prediction',
                            marker: {
                                color: 'rgba(50, 168, 82, 0.95)'
                            }
                        },
                        {
                            x: index_graph_data.slice(input_step-1, realtime_graph_data.length),
                            y: realtime_graph_data.slice(input_step-1, realtime_graph_data.length),
                            type: 'scatter',
                            name: 'Actual',
                            marker: {
                                color: 'rgba(77, 77, 77, 0.35)'
                            }
                        }
                    ];

                    var future_prediction_layout = {
                        title: tag_name,
                        xaxis: {
                            type: 'date',
                            tick0: index_graph_data,
                            tickmode: 'linear',
                            dtick: 2*60*60*1000,
                        },
                        yaxis: {
                            showline: false
                        },
                        showlegend: false
                    };
                    Plotly.newPlot('autoencoder-graph', future_prediction_graph, future_prediction_layout);

                    /* Plotting Metrics */
                    var metrics_graph = [
                        {
                            x: metrics_graph_index,
                            y: metrics_data,
                            type: 'scatter',
                            name: 'Loss',
                            marker: {
                                color: 'rgba(2, 117, 216, 0.95)'
                            }
                        },
                    ];

                    var metrics_layout = {
                        title: tag_name,
                        xaxis: {
                            type: 'date',
                            tick0: metrics_graph_index,
                            tickmode: 'linear',
                            dtick: 2*60*60*1000,
                        },
                        yaxis: {
                            showline: false,
                            tickformat: ',.3%',
                        },
                        showlegend: false
                    };
                    Plotly.newPlot('metrics-graph', metrics_graph, metrics_layout);
                    
                    $('#ovr-metric-value').text((parseFloat(metrics_ovr_loss) * 100).toFixed(2).toString() + "%");
                    $('.metrics-caption').css('visibility', 'visible');
                }
            }}).done(function() {
                $('#loading-modal').modal('hide');
            });
        }
    }

    /* ***************************************** */

    /* Nav Items Configuration */
    $('.nav-item').removeClass("active");
    $('#nav-future-prediction').addClass("active");
    $(".navbar-select-bad-model-time-interval").remove()

    $('#select-tag').on('change', fetch_future_prediction_data);
    $('#date-range-picker').on('apply.daterangepicker', fetch_future_prediction_data);
});