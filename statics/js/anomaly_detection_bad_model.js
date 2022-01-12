$(document).ready(function() {
    /* ***************************************** */
	/* VARIABLE AND FUNCTION DEFINITIONS */

    function fetch_anomaly_detection_bad_model_data() {
        $('#badModelDataTable').dataTable().fnClearTable();
        $('#badModelDataTable').dataTable().fnDraw();
        $('#badModelDataTable').dataTable().fnDestroy();

        $('#badModelDataTable').dataTable({
            "columnDefs": [{ "targets": -1, "data": null, "defaultContent": "<a class='btn btn-info btnView'>View</a>"}]
        });

        unit_value = $('#select-unit').val();
        time_interval_value = $('#select-bad-model-time-interval').val();

        if(time_interval_value != "") {
            $('#loading-modal').modal({
                show: true,
                backdrop: 'static', 
                keyboard: false
            });

            $.ajax({url: "/get_anomaly_detection_bad_model_data",
            data: {'unit': String(unit_value), 
                'time_interval': String(time_interval_value)}, 
            success: function(data){
                if(data.status == 'failed') {
                    alert('FAILED!!\n\n' + data.data)
                }
                else if(data.status == 'success') {
                    $('#div-intro-text').remove();
                    $('#anomaly-bad-model-table').show();

                    bad_model_data = data.data.bad_model_list.data;

                    for (let index = 0; index < bad_model_data.length; index++) {
                        $("<a href='#' class='btn btn-info'>View</a>")
                        newData = [
                            bad_model_data[index][0],
                            bad_model_data[index][1],
                            bad_model_data[index][2],
                            bad_model_data[index][3],
                            bad_model_data[index][4],
                            bad_model_data[index][5],
                        ]
                        $('#badModelDataTable').dataTable().fnAddData(newData);
                    }
                }
            }}).done(function() {
                $('#loading-modal').modal('hide');
            });
        }
    }

    function bad_model_table_clicked() {
        $('#loading-modal').modal({
            show: true,
            backdrop: 'static', 
            keyboard: false
        });
        $('#autoencoder-graph').empty();
        $('#control-limit-graph').empty();

        var data = $('#badModelDataTable').dataTable().api().row($(this).parents('tr')).data();
        unit_value = $('#select-unit').val();
        var date = new Date();
        var date_range_value = moment(date).format('DD/MM/YYYY - DD/MM/YYYY');

        // construct the url
        $.ajax({url: "/get_anomaly_detection_data",
            data: {'unit': String(unit_value), 'tag': data[2], 'date_range': date_range_value}, 
            success: function(data){
                if(data.status == 'failed') {
                    alert('FAILED!!\n\n' + data.data)
                }
                else if(data.status == 'success') {
                    index_data = data.data.realtime.index;
                    realtime_data = data.data.realtime.data;
                    autoencoder_data = data.data.autoencoder.data;
                    lower_limit_data = data.data.lower_limit.data;
                    upper_limit_data = data.data.upper_limit.data;

                    metrics_data = data.data.metrics.data;
                    metrics_index = data.data.metrics.index;
                    metrics_ovr_loss = data.data.metrics.ovr_loss;

                    l1_alarm = data.data.alarm.l1_alarm;
                    h1_alarm = data.data.alarm.h1_alarm;
                    tag_desc = data.data.tag_info.desc;
                    l1_alarm_text = "L1 Alarm: Not Available";
                    h1_alarm_text = "H1 Alarm: Not Available";

                    if (l1_alarm != null) {
                        l1_alarm_text = "L1 Alarm: " + String(l1_alarm);
                    }

                    if (h1_alarm != null) {
                        h1_alarm_text = "H1 Alarm: " + String(h1_alarm);
                    }

                    alarm_text = l1_alarm_text + " | " + h1_alarm_text
                    
                    realtime_graph_data = [];
                    autoencoder_graph_data = [];
                    lower_limit_graph_data = [];
                    upper_limit_graph_data = [];
                    index_graph_data = [];
                    metrics_graph_index = [];

                    for (let index = 0; index < realtime_data.length; index++) {
                        realtime_graph_data.push(realtime_data[index][0]);
                        autoencoder_graph_data.push(autoencoder_data[index][0]);
                        lower_limit_graph_data.push(lower_limit_data[index][0]);
                        upper_limit_graph_data.push(upper_limit_data[index][0]);
                        index_graph_data.push(new Date(index_data[index]));
                    }

                    /* Plotting Autoencoder Performance */
                    var autoencoder_graph = [
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
                        xaxis: {
                            type: 'date',
                            tick0: index_graph_data,
                            tickmode: 'linear',
                            dtick: 2*60*60*1000,
                        },
                        yaxis: {
                            showline: false
                        },
                        showlegend: false,
                        annotations: [
                            {
                              x: 0.5,
                              y: 1.16,
                              xref: 'paper',
                              yref: 'paper',
                              text: tag_desc,
                              showarrow: false,
                              font: {
                                size: 12,
                              },
                            },
                            {
                                x: 0.5,
                                y: 1.06,
                                xref: 'paper',
                                yref: 'paper',
                                text: alarm_text,
                                showarrow: false,
                                font: {
                                  size: 10,
                                },
                            },
                        ]
                    };
                    Plotly.newPlot('autoencoder-graph', autoencoder_graph, autoencoder_layout);

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
                        }
                    ];

                    var control_limit_layout = {
                        title: data.data.realtime.columns[0],
                        xaxis: {
                            type: 'date',
                            tick0: index_graph_data,
                            tickmode: 'linear',
                            dtick: 2*60*60*1000,
                        },
                        yaxis: {
                            showline: false
                        },
                        showlegend: false,
                        annotations: [
                            {
                              x: 0.5,
                              y: 1.16,
                              xref: 'paper',
                              yref: 'paper',
                              text: tag_desc,
                              showarrow: false,
                              font: {
                                size: 12,
                              },
                            },
                            {
                                x: 0.5,
                                y: 1.06,
                                xref: 'paper',
                                yref: 'paper',
                                text: alarm_text,
                                showarrow: false,
                                font: {
                                  size: 10,
                                },
                            },
                        ]
                    };
                    Plotly.newPlot('control-limit-graph', control_limit_graph, control_limit_layout);
                }
            }}).done(function() {
                $('#loading-modal').modal('hide');
                $('#chartModal').modal({
                    show: true, 
                    focus: true
                });
            });
    }

    /* ***************************************** */

    // If current page is anomaly detection bad model, then disable selects
    $(".navbar-select-system").remove()
    $(".navbar-select-equipment").remove()
    $(".navbar-select-tag").remove()
    $(".navbar-date-picker").remove()
    $(".div-bad-model-time-interval").show()

    /* Nav Items Configuration */
    $('.nav-item').removeClass("active");
    $('#nav-group-anomaly-detection').addClass("active");
    $('#nav-bad-model-anomaly-detection').addClass("active");

    $('#select-bad-model-time-interval').on('change', fetch_anomaly_detection_bad_model_data);

    $('#select-unit').select2({
        placeholder: "Select an options",
    });

    $('#select-unit').on('change', function() {
        $("#select-bad-model-time-interval").val('').trigger('change')
    });

    $('#badModelDataTable tbody').on('click', '[class*=btnView]', bad_model_table_clicked);
});