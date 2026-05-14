function UpdateAccount() {
    try {
        var boAcc = TheApplication().GetBusObject("Account");
    var bcAcc = boAcc.GetBusComp("Account");
    var theapp = TheApplication();
    var view = theapp.GetActiveView();
    var a_1 = "";
    var a: Number = 10;
    //var psInputs = ""; var psOutputs = "";

    var lov = TheApplication().InvokeMethod("LookupValue", "TEST_LOV", "TEST_LOV1");

    var testBSInv = vcReadFile.InvokeMethod("ReadEAIMsg", psInputs, psOutputs);


    if (var i = 0; i > 10; i++)
    { }


    // var test ="abc";
    view = "View Name"; var bo, bc, itme1 = "5", item2;
    /*var m1 = 10, m2, m3=20, m4="", m5 = null;*/
    var n1 = 10; /*n3=20, n4="", n5 = null;*/ var n6 = "20";
    var o1 = 10; //no=20=null;
    

    testBSInv(a_1);
    return o1;
    } catch(e) {
        throw e;
    } finally {
        if(defined(o1)) o1 = null;
        if(defined(n6)) n6 = null;
        if(defined(n1)) n1 = null;
        if(defined(item2)) item2 = null;
        if(defined(itme1)) itme1 = null;
        if(defined(bc)) bc = null;
        if(defined(bo)) bo = null;
    
        if(defined(i)) i = null;
        if(defined(testBSInv)) testBSInv = null;
        if(defined(lov)) lov = null;
        if(defined(a)) a = null;
        if(defined(a_1)) a_1 = null;
        if(defined(view)) view = null;
        if(defined(theapp)) theapp = null;
        if(defined(bcAcc)) bcAcc = null;
        if(defined(boAcc)) boAcc = null;
    }

        return (ContinueOperation);
}