renderHomePage = function() {
    bindEventHandlers();
}

bindEventHandlers = function() {
    $('#add_event_button').click(function(){
        $('#add_event_button').hide();
        $('#add_event_form').show('slow');
    });
    $('#submit_add_event_button').click(function(){
        addEvent($('form#add_event_form').getFormData());
        //TODO: redirect
    });
}

addEvent = function(formData) {
    //ajax call to /api/event
    $.post("/api/event", formData, function(newEventData) {
        newEventData = $.parseJSON(newEventData);
        addEventCallback(newEventData);
    });
}

addEventCallback = function(newEventData) {
    window.location.replace("/event/"+newEventData.id);
}

$.fn.getFormData = function() {
    var o = {};
    var a = this.serializeArray();
    $.each(a, function() {
        if (o[this.name] !== undefined) {
            if (!o[this.name].push) {
                o[this.name] = [o[this.name]];
            }
            o[this.name].push(this.value || '');
        } else {
            o[this.name] = this.value || '';
        }
    });
    return o;
}

$(window).load(renderHomePage());
