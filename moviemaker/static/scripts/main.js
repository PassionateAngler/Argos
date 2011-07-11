$(function(){
	var dtpicker_options = {
          dateFormat: 'yy-mm-dd',
	  timeFormat: 'hh:mm'
	}	
	$('#id_start').datetimepicker(dtpicker_options);	
	$('#id_end').datetimepicker(dtpicker_options);	
        
}
);
