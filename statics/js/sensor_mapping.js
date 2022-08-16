$(document).ready(function() {
    /* ***************************************** */
	/* VARIABLE AND FUNCTION DEFINITIONS */

    var sensor_mapping = {};

    function fetch_sensor_mapping(is_update) {
        $('#sensorMappingTable').dataTable().fnClearTable();
        $('#sensorMappingTable').dataTable().fnDraw();
        $('#sensorMappingTable').dataTable().fnDestroy();

        unit_value = $('#select-unit').val();
        $('#loading-modal').modal({
            show: true,
            backdrop: 'static', 
            keyboard: false
        });

        $.ajax({url: "/get_sensor_mapping",
        data: {'is_update': String(is_update)}, 
        success: function(data){
            if(data.status == 'failed') {
                alert('FAILED!!\n\n' + data.data)
            }
            else if(data.status == 'success') {
                $('.intro-text').remove();	
                sensor_mapping.columns = data.data.columns
                sensor_mapping.values = data.data.data

                for (let index = 0; index < sensor_mapping.values.length; index++) {
                    if(sensor_mapping.values[index][0] == String(unit_value)) {
                        newData = [
                            sensor_mapping.values[index][1],
                            sensor_mapping.values[index][2],
                            sensor_mapping.values[index][3],
                            sensor_mapping.values[index][4],
                            sensor_mapping.values[index][5].toString().toUpperCase(),
                        ]
                        $('#sensorMappingTable').dataTable().fnAddData(newData);
                    }
                }
                $('#loading-modal').modal('hide');
            }
        }}).done(function() {
            // $('#loading-modal').modal('hide');
        });
    }

    $('#select-unit').change(function() {
        fetch_sensor_mapping(false);
    });

    $('#update-sensor-mapping').click(function() {
        fetch_sensor_mapping(true);
    });

    /* ***************************************** */

    /* Nav Items Configuration */

    $(".navbar-select-system").remove()
    $(".navbar-select-equipment").remove()
    $(".navbar-select-tag").remove()
    $(".navbar-date-picker").remove()
    
    $('.nav-item').removeClass("active");
    $('#nav-sensor-mapping').addClass("active");
    $(".navbar-select-bad-model-time-interval").remove()
});