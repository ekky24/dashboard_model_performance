$(document).ready(function() {
    /* ***************************************** */
	/* VARIABLE AND FUNCTION DEFINITIONS */

    function fetch_survival_analysis_data() {
        unit_value = $('#select-unit').val();
        equipment_value = $('#select-equipment').val();

        if(equipment_value != "") {
            $('#loading-modal').modal({
                show: true,
                backdrop: 'static', 
                keyboard: false
            });

            $.ajax({url: "/get_survival_analysis_data",
            data: {'unit': String(unit_value), 'equipment': String(equipment_value)}, 
            success: function(data){
                if(data.status == 'failed') {
                    alert('FAILED!!\n\n' + data.data)
                }
                else if(data.status == 'success') {
                    $('.intro-text').remove();

                    index_data = data.data.prediction.data.index;
                    prediction_data = data.data.prediction.data.data;
                    equipment_name = data.data.prediction.equipment_name;
                    
                    prediction_graph_data = [];
                    index_graph_data = [];
                    for (let index = 0; index < prediction_data.length; index++) {
                        prediction_graph_data.push(prediction_data[index][0]);
                        index_graph_data.push(new Date(index_data[index]));
                    }

                    /* Plotting Prediction Plot */
                    var survival_graph = [
                        {
                            x: index_graph_data,
                            y: prediction_graph_data,
                            type: 'scatter',
                            name: 'Survival Function',
                            marker: {
                                color: 'rgba(2, 117, 216, 0.95)'
                            }
                        },
                    ];

                    var survival_layout = {
                        title: equipment_name,
                        xaxis: {
                            type: 'date',
                            tick0: index_graph_data,
                            tickmode: 'linear',
                            dtick: 86400000.0 * 30,
                        },
                        yaxis: {
                            showline: false
                        },
                        showlegend: false
                    };
                    Plotly.newPlot('survival-graph', survival_graph, survival_layout);
                }
            }}).done(function() {
                $('#loading-modal').modal('hide');
            });
        }
    }

    /* ***************************************** */

    // If current page is survival analysis, then disable selects
	$(".navbar-date-picker").remove()
    $(".navbar-select-tag").remove()
    $(".navbar-select-bad-model-time-interval").remove()

    /* Nav Items Configuration */
    $('.nav-item').removeClass("active");
    $('#nav-survival-analysis').addClass("active");

    $('#select-equipment').on('change', fetch_survival_analysis_data);
});