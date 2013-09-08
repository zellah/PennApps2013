var eventData;

renderEventPage = function() {
    bindEventHandlers();
    $.getJSON("/api/event/"+eventID, function(data){
        console.log(data.transactions);
        eventData = data;
        renderTransactions(); 
    });
}

renderTransactions = function() {
    var $trans = $('#all_trans'),
        htmlString = '',
        data = eventData.transactions;
    if (data.length <1) {
        htmlString = "This event has no transactions yet.";
    } else {
        for (var i=0; i<data.length; i++) {
            var amtStr = data[i].amount_cents.toString();
            data[i].amount = amtStr.slice(0,-2)+"."+amtStr.substring(amtStr.length-2, amtStr.length);
            htmlString += "<div id='trans_id_"+data[i].id+"'>"+transTemplate(data[i])+"</div>";
        }
    }
    $trans.html(htmlString);
    bindTransHandlers();
}

bindTransHandlers = function() {
    $('div#all_trans')
        .on("click", "span#trans_desc", function() {
            $(this).parent().find('#collapse_trans').toggle("fast");
        })
        .on("click", '#edit_trans_button', function(){
            $(this).parent().find('div#trans_view').hide();
            $(this).parent().find('div#trans_edit').show();
            $(this).parent().find('#edit_trans_button').hide();
            $(this).parent().find('#edit_trans_button_submit').show();
        })
        .on("click", '#edit_trans_button_submit', function(){
            //TODO: later check if form was changed, for now don't bother
            var el = $(this).parent(),
                $form =el.parent().find('form#edit_trans_form'),
                formData = $form.getFormData();
            //toggle relevant display pieces
            el.find('div#trans_view').show();
            el.find('div#trans_edit').hide();
            el.find('#edit_trans_button').show();
            el.find('#edit_trans_button_submit').hide();
            //convert amount into cents and submit form over ajax
            var loc = formData.amount.indexOf(".");
            if (loc != -1) {
                var val = formData.amount.slice(0, loc)+formData.amount.slice(loc+1, formData.amount.length);
                formData.amount_cents = parseInt(val);
            } else {
                formData.amount_cents = parseInt(formData.amount)*100
            }
            editTrans(formData);
        });
}

bindEventHandlers = function() { 
    var self = this;
    $('#add_trans_button').click(function(){
        $('#add_trans_form').show('slow');
    });
    $('#submit_add_trans_button').click(function(){
        var $form =$('form#add_trans_form'),
            formData = $form.getFormData();
        var loc = formData.amount.indexOf(".");
        if (loc != -1) {
            var val = formData.amount.slice(0, loc)+formData.amount.slice(loc+1, formData.amount.length);
            formData.amount_cents = parseInt(val);
        } else {
            formData.amount_cents = parseInt(formData.amount)*100
        }
        $form.hide('fast');
        $form.find("input[type=text], textarea").val("");
        submitTrans(formData);
    });
    //TODO: js input verification onKeyUp in these inputs
    
    
}

submitTrans = function(formData) {
    //ajax call to /api/transaction
    formData.event_id = eventID;
    delete formData.amount;
    $.post("/api/transaction", formData, function(newTransData) {
        submitTransCallback(newTransData);
    });
}

editTrans = function(data) {
    //ajax call to /api/transaction/<id>
    data.event_id = eventID;
    $.post("/api/transaction/"+data.id, data, function(data) {
        editTransCallback(data);
    });
    
}

submitTransCallback = function(newTransData){
    //TODO: success message:
    //there's a message that lights up and then fades,
    //without resizing anything because mobile

    newTransData = $.parseJSON(newTransData);
    console.log(newTransData);
    eventData.transactions.push(newTransData);
    var amtStr = newTransData.amount_cents.toString();
    newTransData.amount = amtStr.slice(0,-2)+"."+amtStr.substring(amtStr.length-2, amtStr.length);
    var htmlString = "<div id='trans_id_"+newTransData.id+"'>"+transTemplate(newTransData)+"</div>";
    $('#all_trans').append(htmlString);
}

editTransCallback = function(returnData){
    //TODO: success message:
    //there's a message that lights up and then fades,
    //without resizing anything because mobile

    returnData = $.parseJSON(returnData);
    console.log(returnData); 
    //update view based on this
    var $el = $('div#trans_id_'+returnData.id);
    //TODO: also update description once it's editable
    var amtStr = returnData.amount_cents.toString();
    $el.find('span#trans_amount').text(amtStr.slice(0,-2)+"."+amtStr.substring(amtStr.length-2, amtStr.length));
    $el.find('span#trans_vendor').text(returnData.vendor);
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

transTemplate = function(data){
    return '<span id="trans_desc"><h3>'+data.description+'   $<span id="trans_amount">'+data.amount
        +'</span>   <span class="smallH3" style="font-size:10px">'+data.created+'</span></h3></span>'
        //collapsed info
        +'<div id="collapse_trans" style="display: none">'
        +'<div id="trans_view">'
            +'On <span id="trans_date">'+data.created+'</span>, '
            +'<span id="trans_creator">'+data.creator.name+'</span> spent '
            +'$<span id="trans_amount">'+data.amount+'</span> at '
            +'<span id="trans_vendor">'+data.vendor+'</span> on '
            +'<span id="trans_desc">'+data.description+'</span>'
        +'</div>'
        //edit form
        +'<div id="trans_edit" data-node-value='+data.id+' style="display: none">'
        +'<form id="edit_trans_form">'
            +'<input type="hidden" name="id" value="'+data.id+'">'
            +'<span id="trans_creator">'+data.creator.name+'</span> spent '
            +'$<input type="text" name="amount" value="'+data.amount+'"> at '
            +'<input type="text" name="vendor" value="'+data.vendor+'">'
            //TODO: edit description
        +'</form></div>'
        +'<button type="button" id="edit_trans_button">Edit</button>'
        +'<button type="button" id="edit_trans_button_submit" style="display: none">Submit</button>'
        +'</div>';
}

$(window).load(renderEventPage());
