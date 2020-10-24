$(document).ready(function() {
    $('.vTextField').width(200);
    for(let i = 0; i < $( ".field-field_type select" ).length; i++) {
        $('#id_testsheetfield_set-' + i + '-field_type').change(function(){
            if($(this).val() == 3) {
                $('#id_testsheetfield_set-' + i + '-field_range_or_selective').attr("style", "pointer-events: none; background-color: #eee;");
                $('#id_testsheetfield_set-' + i + '-field_range').attr("style", "pointer-events: none; background-color: #eee;");
            }
            else {
                $('#id_testsheetfield_set-' + i + '-field_range_or_selective').attr("style", "pointer-events: auto; background-color: #fff;");
                $('#id_testsheetfield_set-' + i + '-field_range').attr("style", "pointer-events: auto; background-color: #fff;");
            }
        });
    }
});