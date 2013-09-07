renderEventPage = function($el) {
    var eventID = 0,
        getTransdata = {
            url: "/api/event/"+eventID
        }
    bindEventHandlers($el);
    /*
    $.getJSON(getTransdata, function(data){
        renderTransactions(data);
    });
    */
    renderTransactions();
}

renderTransactions = function(dataIn) {
    //temp
    var $trans = $('#all_trans'),
        htmlString = '',
        data = [
            {
                id:"123",
                description:"pizza",
                creator:"me",
                vendor:"That one place down the street",
                amount:"1234",
                name:"" //TODO: will eventually have list of people, format unknown, ask Nathan
            },
            {
                id:"456",
                description:"soda",
                creator:"spiderman",
                vendor:"A pricey vending machine",
                amount:"4000",
                name:"" //TODO: will eventually have list of people, format unknown, ask Nathan
            }
        ]
    if (data.length <1) {
        htmlString = "This event has no transactions yet.";
    } else {
        for (var i=0; i<data.length; i++) {
            htmlString += "<div id=trans_"+i+" >"+transTemplate(data[i])+"</div>";
        }
    }
    console.log($trans);
    $trans.html(htmlString);
}

bindEventHandlers = function($el) { //do I need delegate? if so, TODO
    var self = this;
    $('#add_trans_button').click(function(){
        $('#add_trans_form').show('slow');
    });
    $('#submit_add_trans_button').click(function(){
        var $form =$('form#add_trans_form'),
            data = $form.getFormData();
        //TODO: parse amount into integer
        //TODO: default Vendor and Desc input with examples maybe
        $form.hide('fast');
        $form.find("input[type=text], textarea").val("");
        submitTrans(data);
    });
    //TODO: js input verification onKeyUp in these inputs
    
    
}

submitTrans = function(data) {
    //ajax call to /api/transaction
    var self = this,
        postData = {
            url: "/api/transaction",
            type: "POST",
            data: data
        }
    data.eventID = "eventID"; //TODO
    console.log(data);
    $.post(postData, function(data) {
        submitTransCallback(data);
    });
}

submitTransCallback = function(returnData){
    //there's a message that lights up and then fades,
    //without resizing anything because mobile
    console.log("Add Transcation Success");
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
    //TODO: parse amount back into xx.xx
    return '<span id="trans_creator">'+data.creator+'</span> spent '
        +'$<span id="trans_amount">'+data.amount+'</span> at '
        +'<span id="trans_vendor">'+data.vendor+'</span> on '
        +'<span id="trans_desc"><h3>'+data.description+'</h3></span>';
}

$(window).load(renderEventPage($(window)));
