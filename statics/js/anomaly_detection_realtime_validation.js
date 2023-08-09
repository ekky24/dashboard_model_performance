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

        if(unit_value != "") {
            $('#loading-modal').modal({
                show: true,
                backdrop: 'static', 
                keyboard: false
            });

            $.ajax({url: "/get_anomaly_detection_realtime_validation_data",
            data: {'unit': String(unit_value), 
                'date_range': String(date_range_value)}, 
            success: function(data){
                if(data.status == 'failed') {
                    alert('FAILED!!\n\n' + data.data)
                }
                else if(data.status == 'success') {
                    $('#download-table').attr('href', 'http://35.219.48.62/bad_model_table_dump/'+String(unit_value)+'.csv')

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

    /* ***************************************** */

    // If current page is anomaly realtime validation, then disable selects
    $(".navbar-select-system").remove()
    $(".navbar-select-equipment").remove()
    $(".navbar-select-tag").remove()
    $(".navbar-select-bad-model-time-interval").remove()

    /* Nav Items Configuration */
    $('.nav-item').removeClass("active");
    $('#nav-group-anomaly-detection').addClass("active");
    $('#nav-realtime-validation-anomaly-detection').addClass("active");

    $('#select-unit').on('change', fetch_anomaly_detection_realtime_validation_data);
    $('#date-range-picker').on('apply.daterangepicker', fetch_anomaly_detection_realtime_validation_data);
});