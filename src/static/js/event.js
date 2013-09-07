renderEventPage = function() {
    bindEventHandlers();
    
    $.getJSON("/api/event/"+eventID, function(data){
        console.log(data.transactions);
        renderTransactions(data); 
    });
}

renderTransactions = function(dataIn) {
    var $trans = $('#all_trans'),
        htmlString = '',
        data = dataIn.transactions;
    if (data.length <1) {
        htmlString = "This event has no transactions yet.";
    } else {
        for (var i=0; i<data.length; i++) {
            var amtStr = data[i].amount_cents.toString();
            data[i].amount = amtStr.slice(0,-2)+"."+amtStr.substring(amtStr.length-2, amtStr.length);
            htmlString += "<div id=trans_"+i+" >"+transTemplate(data[i])+"</div>";
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
            var el = $(this),
                $form =el.parent().find('form#edit_trans_form'),
                data = $form.getFormData();
            //toggle relevant display pieces
            el.parent().find('div#trans_view').show();
            el.parent().find('div#trans_edit').hide();
            el.parent().find('#edit_trans_button').show();
            el.parent().find('#edit_trans_button_submit').hide();
            //convert amount into cents and submit form over ajax
            var loc = data.amount.indexOf(".");
            if (loc != -1) {
                var val = data.amount.slice(0, loc)+data.amount.slice(loc+1, data.amount.length);
                data.amount_cents = parseInt(val);
            } else {
                data.amount_cents = parseInt(val)*100
            }
            var id = 0; //TODO: put in form as hidden field
            submitTransEdit(data, id);
        });
}

bindEventHandlers = function() { 
    var self = this;
    $('#add_trans_button').click(function(){
        $('#add_trans_form').show('slow');
    });
    $('#submit_add_trans_button').click(function(){
        var $form =$('form#add_trans_form'),
            data = $form.getFormData();
        var loc = data.amount.indexOf(".");
        if (loc != -1) {
            var val = data.amount.slice(0, loc)+data.amount.slice(loc+1, data.amount.length);
            data.amount_cents = parseInt(val);
        } else {
            data.amount_cents = parseInt(data.amount)*100
        }
        $form.hide('fast');
        $form.find("input[type=text], textarea").val("");
        submitTrans(data);
    });
    //TODO: js input verification onKeyUp in these inputs
    
    
}

submitTrans = function(data) {

    //TODO: TypeError: 'participants[]' is an invalid keyword argument for Transaction

    //ajax call to /api/transaction
    data.event_id = eventID;
    delete data.amount;
    console.log(data);
    console.log(data.participants);
    $.post("/api/transaction", data, function(ret) {
        console.log(ret)
        submitTransCallback(ret);
    });
}

submitTransEdit = function(data, id) {
    //ajax call to /api/transaction/<id>
    data.event_id = eventID;
    console.log(data);
    $.post("/api/transaction"+id, data, function(data) {
        editTransCallback(data);
    });
    
}

submitTransCallback = function(returnData){
    //there's a message that lights up and then fades,
    //without resizing anything because mobile
    console.log("Add Transcation Success");
    //TODO: either re-render or manually add the new transaction
}

editTransCallback = function(returnData){
    //there's a message that lights up and then fades,
    //without resizing anything because mobile
    console.log("Edit Transcation Success");
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
    return '<span id="trans_desc"><h3>'+data.description+'   $'+data.amount
        +'   <span class="smallH3" style="font-size:10px">'+data.created+'</span></h3></span>'
        //collapsed info
        +'<div id="collapse_trans" style="display: none" data-node-value='+data.id+'>'
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
            +'On <input type="text" name="date" value="'+data.created+'">, '
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
