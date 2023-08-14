$(document).ready(function() {
    /* ***************************************** */
	/* VARIABLE AND FUNCTION DEFINITIONS */

    function fetch_anomaly_detection_realtime_validation_data() {
        $('#badModelDataTable').dataTable().fnClearTable();
        $('#badModelDataTable').dataTable().fnDraw();
        $('#badModelDataTable').dataTable().fnDestroy();

        $('#badModelDataTable').dataTable({
            "columnDefs": [{ "targets": -1, "data": null, "defaultContent": "<a class='btn btn-info btnView'>View</a>"}]
        });

        unit_value = $('#select-unit').val();
        date_range_value = $('#date-range-picker').val();
        type_value = $('#select-realtime-validation-type').val();
        threshold_value = ""

        if(type_value == 'big_anomaly_count') {
            threshold_value = $("#perc_threshold").val()
        }
        else if(type_value == 'limit_small' || type_value == 'limit_big') {
            threshold_value = $("#limit_threshold").val()
        }

        if(unit_value != "") {
            $('#loading-modal').modal({
                show: true,
                backdrop: 'static', 
                keyboard: false
            });

            $.ajax({url: "/get_anomaly_detection_realtime_validation_data",
            data: {'unit': String(unit_value), 
                'date_range': String(date_range_value),
                'type_value': String(type_value),
                'threshold_value': String(threshold_value)}, 
            success: function(data){
                if(data.status == 'failed') {
                    alert('FAILED!!\n\n' + data.data)
                }
                else if(data.status == 'success') {
                    $('#download-table').attr('href', 'http://35.219.48.62/anomaly_realtime_validation_dump/'+String(unit_value)+'_'+String(type_value)+'.csv')

                    $('#div-intro-text').remove();
                    $('#div-download-table').show();
                    $('#anomaly-bad-model-table').show();

                    bad_model_data = data.data.bad_model_list.data;

                    for (let index = 0; index < bad_model_data.length; index++) {
                        $("<a href='#' class='btn btn-info'>View</a>")
                        newData = [
                            bad_model_data[index][0],
                            bad_model_data[index][1],
                            bad_model_data[index][2],
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
                    tag_desc = data.data.tag_info.desc;
                    
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

    function change_threshold_layout() {
        type_value = $('#select-realtime-validation-type').val();

        if(type_value == 'big_anomaly_count') {
            $(".div-parent-threshold").show()
            $(".div-perc-threshold").show()
            $(".div-limit-threshold").hide()
            $(".div-flat-data").hide()
        }
        else if(type_value == 'limit_small' || type_value == 'limit_big') {
            $(".div-parent-threshold").show()
            $(".div-perc-threshold").hide()
            $(".div-limit-threshold").show()
            $(".div-flat-data").hide()
        }
        else if(type_value == 'flat_data') {
            $(".div-parent-threshold").show()
            $(".div-perc-threshold").hide()
            $(".div-limit-threshold").hide()
            $(".div-flat-data").show()
        }

        $("#perc_threshold").val("")
        $("#limit_threshold").val("")
    }

    /* ***************************************** */

    // If current page is anomaly realtime validation, then disable selects
    $(".navbar-select-system").remove()
    $(".navbar-select-equipment").remove()
    $(".navbar-select-tag").remove()
    $(".navbar-select-bad-model-time-interval").remove()

    $(".div-parent-threshold").hide()
    $(".div-limit-threshold").hide()
    $(".div-perc-threshold").hide()
    $(".div-flat-data").hide()

    /* Nav Items Configuration */
    $('.nav-item').removeClass("active");
    $('#nav-group-anomaly-detection').addClass("active");
    $('#nav-realtime-validation-anomaly-detection').addClass("active");

    $('.realtime-validation-search').on('click', fetch_anomaly_detection_realtime_validation_data);
    $('#select-realtime-validation-type').on('change', change_threshold_layout);

    $('#badModelDataTable tbody').on('click', '[class*=btnView]', bad_model_table_clicked);
});