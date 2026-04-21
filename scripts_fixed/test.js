function UpdateAccount() {
        var boAcc = TheApplication().GetBusObject("Account");
    var bcAcc = boAcc.GetBusComp("Account");
    var theapp = TheApplication();
    var view = theapp.GetActiveView();
    var a:Number = 10;
   // var test ="abc";
    view="View Name"; var bo, bc, itme1, item2;
    /*var m1 = 10, m2, m3=20, m4="", m5 = null;*/
    var n1 = 10; /*n3=20, n4="", n5 = null;*/ var n6="20";
    var o1 = 10; //no=20=null;
    var a_1, a_2;
    var a_3;

        //var psInputs = ""; var psOutputs = "";
var lov = TheApplication().InvokeMethod("LookupValue","TEST_LOV","TEST_LOV1");
                var testBSInv = vcReadFile.InvokeMethod("ReadEAIMsg", psInputs, psOutputs);
if (var i=0; i>10; i++)
    
    try {
        var x="";
        var x="", y="12", z="", a="";
        bcAcc.WriteRecord();
        

    } catch(e) {
        throw e;
    }var abc="";
    finally {
        bcAcc = null;
        x=null;
        
    
        if(defined(abc)) abc = null;
        if(defined(z)) z = null;
        if(defined(y)) y = null;
        if(defined(x)) x = null;
        if(defined(i)) i = null;
        if(defined(lov)) lov = null;
        if(defined(a_3)) a_3 = null;
        if(defined(n6)) n6 = null;
        if(defined(n1)) n1 = null;
        if(defined(item2)) item2 = null;
        if(defined(itme1)) itme1 = null;
        if(defined(bc)) bc = null;
        if(defined(bo)) bo = null;
        if(defined(a)) a = null;
        if(defined(view)) view = null;
        if(defined(theapp)) theapp = null;
        if(defined(bcAcc)) bcAcc = null;
        if(defined(boAcc)) boAcc = null;
    }
    testBSInv(a_1, a_2);
    return o1;
}