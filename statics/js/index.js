$(document).ready(function() {
    /* ***************************************** */
	/* VARIABLE AND FUNCTION DEFINITIONS */

    function fetch_raw_data() {
        tag_value = $('#select-tag').val();
        unit_value = $('#select-unit').val();
        date_range_value = $('#date-range-picker').val();

        if(tag_value != "" && date_range_value != "") {
            $('#loading-modal').modal({
                show: true,
                backdrop: 'static', 
                keyboard: false
            });

            $.ajax({url: "/get_raw_data",
            data: {'unit': String(unit_value), 'tag': String(tag_value), 'date_range': String(date_range_value)}, 
            success: function(data){
                $('.intro-text').remove();

                parse_data = JSON.parse(data.data.realtime.data)
                index_data = parse_data.index;
                realtime_data = parse_data.data;
                n_normal = data.data.realtime.n_normal;
                n_null = data.data.realtime.n_null;
                n_outlier = data.data.realtime.n_outlier;

                stat_desc_mean = data.data.stat_desc.mean;
                stat_desc_std_dev = data.data.stat_desc.std_dev;
                stat_desc_q1 = data.data.stat_desc.q1;
                stat_desc_median = data.data.stat_desc.median;
                stat_desc_q3 = data.data.stat_desc.q3;
                stat_desc_minimum = data.data.stat_desc.minimum;
                stat_desc_maximum = data.data.stat_desc.maximum;

                realtime_graph_data = [];

                for (let index = 0; index < realtime_data.length; index++) {
                    realtime_graph_data.push(realtime_data[index][0]);
                } 
                
                /* Plotting Raw Data */
                var realtime_graph = [
                    {
                        x: index_data,
                        y: realtime_graph_data,
                        type: 'scatter',
                        name: 'Raw Data',
                        marker: {
                            color: 'rgba(2, 117, 216, 0.95)'
                        }
                    },
                ];

                var realtime_layout = {
                    title: parse_data.columns[0],
                    yaxis: {
                        showline: false
                    },
                    showlegend: false
                };
                Plotly.newPlot('raw-graph', realtime_graph, realtime_layout);

                /* Plotting Data Health Info */
                var health_info_graph = [
                    {
                        x: [n_outlier, n_null, n_normal],
                        y: ['Outlier', 'Null Values', 'Normal'],
                        type: 'bar',
                        orientation: 'h',
                        marker: {
                            color: ['rgba(231, 74, 59, 0.95)', 'rgba(246, 194, 62, 0.95)', 'rgba(2, 117, 216, 0.95)']
                        }
                    },
                ];

                var health_info_layout = {
                    title: parse_data.columns[0],
                    xaxis: {
                        showline: false,
                        tickformat: ',.2%'
                    },
                    showlegend: false
                };
                Plotly.newPlot('health-info-graph', health_info_graph, health_info_layout);

                /* Showing Stat Descriptive */
                $('#stat-desc-mean').text(stat_desc_mean);
                $('#stat-desc-std-dev').text(stat_desc_std_dev);
                $('#stat-desc-q1').text(stat_desc_q1);
                $('#stat-desc-median').text(stat_desc_median);
                $('#stat-desc-q3').text(stat_desc_q3);
                $('#stat-desc-minimum').text(stat_desc_minimum);
                $('#stat-desc-maximum').text(stat_desc_maximum);

            }}).done(function() {
                $('#loading-modal').modal('hide');
            });
        }
    }

    /* ***************************************** */

    /* Nav Items Configuration */
    $('.nav-item').removeClass("active");
    $('#nav-raw-data').addClass("active");

    $('#select-tag').on('change', fetch_raw_data);
    $('#date-range-picker').on('apply.daterangepicker', fetch_raw_data);
});