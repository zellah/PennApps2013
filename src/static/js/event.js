var eventData;
var users=[];
var selectUsers="";

renderEventPage = function() {
    bindEventHandlers();
    $.getJSON("/api/event/"+eventID, function(data){
        eventData = data;
        renderTransactions();
        //add users to global users var
        for (var i=0; i<eventData.participants.length; i++) {
            users[i]=(eventData.participants[i].name);
        }
        $('#participant_checkboxes').html(genSelectUsers());
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
            $(this).parent().find('div#trans_view').hide('slow');
            $(this).parent().find('div#trans_edit').show('slow');
            $(this).parent().find('#edit_trans_button').hide();
            $(this).parent().find('#edit_trans_button_submit').show('fast');
            $(this).parent().find('#edit_trans_button_cancel').show('fast');
            $(this).parent().find('#del_trans_button').show('fast');
        })
        .on("click", '#edit_trans_button_cancel', function(){
            $(this).parent().find('div#trans_view').show('slow');
            $(this).parent().find('div#trans_edit').hide('slow');
            $(this).parent().find('#edit_trans_button').show('fast');
            $(this).parent().find('#edit_trans_button_submit').hide();
            $(this).parent().find('#edit_trans_button_cancel').hide();
            $(this).parent().find('#del_trans_button').hide();
        })
        .on("click", '#del_trans_button', function(){
            var $form =$(this).parent().parent().find('form#edit_trans_form'),
                formData = $form.getFormData();
            delTrans(formData.id);
        })
        .on("click", '#edit_trans_button_submit', function(){
            //TODO: later check if form was changed, for now don't bother
            var el = $(this).parent(),
                $form =el.parent().find('form#edit_trans_form'),
                formData = $form.getFormData();
            //toggle relevant display pieces
            el.find('div#trans_view').show('slow');
            el.find('div#trans_edit').hide('slow');
            el.find('#edit_trans_button').show('fast');
            el.find('#edit_trans_button_submit').hide();
            el.find('#edit_trans_button_cancel').hide();
            el.find('#del_trans_button').hide();
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
    $('#add_trans_button_cancel').click(function(){
        $('#add_trans_form').hide('slow');
    });
    $('#add_user_button').click(function(){
        $('#add_user_form').show('slow');
    });
    $('#cancel_add_user_button').click(function(){
        $('#add_user_form').hide('slow');
    });
    $('#submit_add_user_button').click(function(){
        tryAddUser($('input#email').val());
    });
    $('#cancel_add_trans_button').click(function(){
        $('form#add_trans_form').hide('slow');
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

tryAddUser = function(email) {
    //ajax call to /api/transaction
    $.post("/api/event/"+eventID+"/adduser", {email:email}, function(retVal) {
        retVal = $.parseJSON(retVal);
        console.log(retVal);
        tryAddUserCallback(retVal);
    });
}

tryAddUserCallback = function(retVal) {
    console.log(retVal.error);
    if (retVal.error) {
        alert("No user with that email address exists in our database.");
    } else {
        //TODO: add user to all trans inputs
    }
}

submitTrans = function(formData) {
    //ajax call to /api/transaction
    formData.event_id = eventID;
    delete formData.amount;
    $.post("/api/transaction", formData, function(newTransData){
        submitTransCallback(newTransData);
    });
}

editTrans = function(data) {
    //ajax call to /api/transaction/<id>
    data.event_id = eventID;

console.log(data);

    $.post("/api/transaction/"+data.id, data, function(newTransData){
        editTransCallback(newTransData);
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
    $el.find('span#trans_desc').text(returnData.description);
}

delTrans = function(transID){
    //TODO: confirm desire to delete
    data = {'del_transactions':transID};
    $.post("/api/event/"+eventData.id, data, function(returnData){
        $('div#trans_id_'+transID).remove()
    })
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

genSelectUsers = function() {
    var htmlString="";
    for (var i=0; i<eventData.participants.length; i++) {
            htmlString+= '<input type="checkbox" name="participants" value="'
                    +eventData.participants[i].id+'" checked>'
                    +eventData.participants[i].name;
    }
    selectUsers = htmlString;
    return selectUsers;
}

var myData;

genTransSelect = function(participants) {
    myData = participants;
    var htmlString="";
    for (var i=0; i<eventData.participants.length; i++) {
            htmlString+= '<input type="checkbox" name="participants" value="'
                    +eventData.participants[i].id+'"';
            for (var j=0; j<participants.length; j++){
                if (participants[j].id == eventData.participants[i].id){
                    htmlString+=' checked';
                }
            }
            htmlString+= '>'+eventData.participants[i].name+' ';
    }
    return htmlString;
}

transTemplate = function(data){
    var select = genTransSelect(data.participants);
    return '<span id="trans_desc" class=""><h3>'
        +'<span id="trans_desc">'+data.description+'</span>'
        +'   $<span id="trans_amount">'+data.amount
        +'</span>   <span class="smallH3" style="font-size:10px">'+data.created+'</span></h3></span>'
        //collapsed info
        +'<div id="collapse_trans" style="display: none">'
        +'<div id="trans_view">'
            +'<span id="trans_creator">'+data.creator.name+'</span> spent '
            +'$<span id="trans_amount">'+data.amount+'</span> at '
            +'<span id="trans_vendor">'+data.vendor+'</span> on '
            +'<span id="trans_descr">'+data.description+'</span>'
        +'</div>'
        //edit form
        +'<div id="trans_edit" data-node-value='+data.id+' style="display: none">'
        +'<form id="edit_trans_form">'
            +'<input type="hidden" name="id" value="'+data.id+'">'
            +'<span id="trans_creator">'+data.creator.name+'</span> spent '
            +'$<input type="text" name="amount" value="'+data.amount+'"></br>on '
            +'<input type="text" name="description" value="'+data.description+'"></br>at '
            +'<input type="text" name="vendor" value="'+data.vendor+'"><br/>for '
            +select
        +'</form></div>'
        +'<button type="button" id="edit_trans_button" class="btn btn-mini">Edit</button>'
        +'<button type="button" id="edit_trans_button_submit" class="btn btn-mini" style="display: none">Submit</button>    '
        +'<button type="button" id="edit_trans_button_cancel" class="btn btn-mini" style="display: none">Cancel</button>    '
        +'<button type="button" id="del_trans_button" class="btn btn-mini" style="display: none">Delete</button>    '   
        +'</div>';
}

$(window).load(renderEventPage());
