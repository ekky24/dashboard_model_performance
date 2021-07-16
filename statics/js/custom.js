$(document).ready(function() {
	/* ***************************************** */
	/* VARIABLE AND FUNCTION DEFINITIONS */

	var sensor_mapping = {};

	Array.prototype.contains = function(v) {
		for (var i = 0; i < this.length; i++) {
			if (this[i] === v) return true;
		}
		return false;
	};

	Array.prototype.unique = function() {
		var arr = [];
		for (var i = 0; i < this.length; i++) {
			if (!arr.contains(this[i])) {
				arr.push(this[i]);
			}
		}
		return arr;
	}

	function topbar_select_changer(elem) {
		unit_value = $('#select-unit').val()
		system_value = $('#select-system').val()
		equipment_value = $('#select-equipment').val()
		tag_value = $('#select-tag').val()
		
		if(elem.target.id == 'select-unit') {
			systems = []
			for (let index = 0; index < sensor_mapping.values.length; index++) {
				if(sensor_mapping.values[index][0] == unit_value) {
					systems.push(sensor_mapping.values[index][1])
				}
			}
	
			systems = systems.unique();
			$('#select-system').empty().append(new Option());
			$('#select-equipment').empty().append(new Option());
			$('#select-tag').empty().append(new Option());
			for (let index = 0; index < systems.length; index++) {
				$('#select-system').append(new Option(systems[index], systems[index]));
			}
		}
		else if(elem.target.id == 'select-system') {
			equipments = []
			for (let index = 0; index < sensor_mapping.values.length; index++) {
				if(sensor_mapping.values[index][0] == unit_value && 
					sensor_mapping.values[index][1] == system_value) {

					equipments.push(sensor_mapping.values[index][2])
				}
			}

			equipments = equipments.unique();
			$('#select-equipment').empty().append(new Option());
			$('#select-tag').empty().append(new Option());
			for (let index = 0; index < equipments.length; index++) {
				$('#select-equipment').append(new Option(equipments[index], equipments[index]));
			}
		}
		else if(elem.target.id == 'select-equipment') {
			tags = []
			for (let index = 0; index < sensor_mapping.values.length; index++) {
				if(sensor_mapping.values[index][0] == unit_value && 
					sensor_mapping.values[index][1] == system_value && 
					sensor_mapping.values[index][2] == equipment_value) {

					tags.push(sensor_mapping.values[index][3])
				}
			}

			tags = tags.unique();
			$('#select-tag').empty().append(new Option());
			for (let index = 0; index < tags.length; index++) {
				$('#select-tag').append(new Option(tags[index], tags[index]));
			}
		}
	}

	/* ***************************************** */

	$('.searchable-select').select2({
		placeholder: "Select an option",
	});
	$('.date-range-picker').daterangepicker({
		locale: {
			format: 'DD/MM/YYYY'
		}
	});

	$('#select-unit').on('change', topbar_select_changer);
	$('#select-system').on('change', topbar_select_changer);
	$('#select-equipment').on('change', topbar_select_changer);
	$('#select-tag').on('change', topbar_select_changer);

	$('#loading-modal').modal({
		show: true,
		backdrop: 'static', 
		keyboard: false
	});

	$.ajax({url: "/get_sensor_mapping",
	success: function(data){		
		sensor_mapping.columns = data.data.columns
		sensor_mapping.values = data.data.data
		units = []
		
		for (let index = 0; index < sensor_mapping.values.length; index++) {
			units.push(sensor_mapping.values[index][0])
		}

		units = units.unique();
		
		for (let index = 0; index < units.length; index++) {
			$('#select-unit').append(new Option(units[index], units[index]));
		}
	}}).done(function() {
		$('#loading-modal').modal('hide');
	});
});